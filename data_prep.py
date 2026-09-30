import pandas as pd
import numpy as np

print("Baixando e processando os dados. Isso pode levar alguns segundos...")

# URL direta do arquivo CSV no Google Drive, de 2026
csv_url = "https://drive.google.com/uc?id=1exU-ynijoUW0MwGj7LOk1NDYuHtaGNru"

# 1. Carregar os dados diretamente da URL
df = pd.read_csv(csv_url, sep=';', encoding='latin1')

# 2. Filtrar estado do Rio de Janeiro (equivalente ao WHERE uf = 'RJ')
df_rj = df[(df['uf'] == 'RJ') & (df['br'] > 0)].copy()

# 3. Tratamento de campos numéricos e conversão de vírgula para ponto
df_rj['latitude'] = df_rj['latitude'].astype(str).str.replace(',', '.').astype(float)
df_rj['longitude'] = df_rj['longitude'].astype(str).str.replace(',', '.').astype(float)
df_rj['km'] = df_rj['km'].astype(str).str.replace(',', '.').astype(float)

# 4. Criar identificação padronizada do corredor
df_rj['nome_corredor'] = "BR-" + df_rj['br'].astype(str).str.zfill(3)

# 5. Extração da hora para análise temporal (Corrigido para df_rj)
df_rj['hora'] = pd.to_datetime(df_rj['horario'], format='%H:%M:%S').dt.hour

# 6. Criar novas métricas (Movido para ANTES de salvar o CSV)
df_rj['total_feridos'] = df_rj['feridos_graves'] + df_rj['feridos_leves']

# 7. Salvar base tratada
df_rj.to_csv('datatran2026_rj.csv', index=False)

print(f"Total de registros processados no RJ: {len(df_rj)}")
print("Arquivo 'datatran2026_rj.csv' gerado com sucesso!")