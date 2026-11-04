"""Cálculo das "áreas de risco": batidas mais distantes de unidades de saúde, agrupadas por proximidade.

Só usa numpy/pandas (sem streamlit), pra poder ser testado e reaproveitado fora do dashboard.
"""

import numpy as np
import pandas as pd

RAIO_TERRA_KM = 6371.0088
KM_POR_GRAU_LAT = 111.32

# Valores padrão, calibrados nos dados de 2026.1 (jan-jul), RJ, 3776 batidas e 614 unidades:
# - TOP_N_PADRAO = 100: corta em ~13,7 km da unidade mais próxima (~2,6% das batidas). Com 50 o corte
#   sobe pra 16 km e só sobram 11 áreas; com 200+ entram batidas a ~12 km, que já são menos críticas.
# - LIMITE_KM_PADRAO = 2: fica no "platô" do agrupamento (de 1,5 a 2 km o resultado não muda). Acima de
#   ~3 km começa o encadeamento: áreas distintas são fundidas e o retângulo passa de 6 km para 24+ km.
# - MIN_BATIDAS_PADRAO = 2: uma batida isolada não é uma "área onde ocorrem várias".
TOP_N_PADRAO = 100
LIMITE_KM_PADRAO = 2.0
MIN_BATIDAS_PADRAO = 2


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distância em km entre pontos (aceita arrays; faz broadcast)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


def distancia_ate_unidade_mais_proxima(acidentes, unidades, bloco=2000):
    """Para cada acidente, a distância (km, em linha reta) até a unidade de saúde mais próxima.

    Processa em blocos de acidentes pra não montar uma matriz gigante quando a base crescer.
    """
    lat = acidentes["latitude"].to_numpy(dtype=float)
    lon = acidentes["longitude"].to_numpy(dtype=float)
    lat_u = unidades["latitude"].to_numpy(dtype=float)
    lon_u = unidades["longitude"].to_numpy(dtype=float)

    distancias = np.empty(len(lat))
    for i in range(0, len(lat), bloco):
        d = _haversine_km(lat[i:i + bloco, None], lon[i:i + bloco, None], lat_u[None, :], lon_u[None, :])
        distancias[i:i + bloco] = d.min(axis=1)
    return distancias


def agrupar_por_proximidade(lat, lon, limite_km):
    """Rótulo de grupo pra cada ponto: dois pontos a até `limite_km` um do outro ficam no mesmo grupo.

    É o encadeamento (single linkage): se A está perto de B e B perto de C, os três formam uma
    área só, mesmo que A e C estejam mais longe que o limite entre si.
    """
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    n = len(lat)
    vizinhos = _haversine_km(lat[:, None], lon[:, None], lat[None, :], lon[None, :]) <= limite_km

    rotulos = np.full(n, -1)
    grupo = 0
    for inicio in range(n):
        if rotulos[inicio] != -1:
            continue
        fila = [inicio]
        rotulos[inicio] = grupo
        while fila:
            atual = fila.pop()
            for v in np.flatnonzero(vizinhos[atual] & (rotulos == -1)):
                rotulos[v] = grupo
                fila.append(v)
        grupo += 1
    return rotulos


def areas_de_risco(
    acidentes, unidades, top_n=TOP_N_PADRAO, limite_km=LIMITE_KM_PADRAO,
    min_batidas=MIN_BATIDAS_PADRAO, margem_km=1.0,
):
    """Pega as `top_n` batidas mais longe de unidades de saúde e as agrupa em retângulos.

    Devolve (batidas_top, areas):
      - batidas_top: as top_n batidas, com a coluna `dist_unidade_km` e `area` (id do grupo)
      - areas: um retângulo por grupo, com coluna `polygon` ([lon, lat] dos 4 cantos) e estatísticas.
    Áreas com menos de `min_batidas` batidas não viram retângulo (a batida continua em `batidas_top`).
    `margem_km` engorda o retângulo, senão uma batida isolada (ou duas alinhadas) viraria só uma linha.
    """
    if acidentes.empty or unidades.empty:
        return acidentes.iloc[0:0].assign(dist_unidade_km=[], area=[]), pd.DataFrame()

    com_dist = acidentes.assign(
        dist_unidade_km=distancia_ate_unidade_mais_proxima(acidentes, unidades)
    )
    top = com_dist.nlargest(top_n, "dist_unidade_km").copy()
    top["area"] = agrupar_por_proximidade(top["latitude"], top["longitude"], limite_km)

    linhas = []
    for area, g in top.groupby("area"):
        if len(g) < min_batidas:
            continue
        lat_c = g["latitude"].mean()
        d_lat = margem_km / KM_POR_GRAU_LAT
        d_lon = margem_km / (KM_POR_GRAU_LAT * np.cos(np.radians(lat_c)))
        sul, norte = g["latitude"].min() - d_lat, g["latitude"].max() + d_lat
        oeste, leste = g["longitude"].min() - d_lon, g["longitude"].max() + d_lon
        linhas.append(
            {
                "area": area,
                "polygon": [[oeste, sul], [leste, sul], [leste, norte], [oeste, norte]],
                "n_batidas": len(g),
                "dist_media_km": g["dist_unidade_km"].mean(),
                "dist_max_km": g["dist_unidade_km"].max(),
                "rodovias": ", ".join(sorted(g["nome_corredor"].dropna().unique())),
                "municipios": ", ".join(sorted(g["municipio"].dropna().unique())),
                "mortos": int(g["mortos"].sum()),
                "feridos": int(g["feridos"].sum()),
            }
        )
    if not linhas:
        return top, pd.DataFrame()
    areas = pd.DataFrame(linhas).sort_values("n_batidas", ascending=False, ignore_index=True)
    return top, areas
