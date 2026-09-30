# Projeto Oasis - Dashboard de Acidentes RJ

Painel interativo construído em Streamlit para análise de acidentes nas rodovias federais do Rio de Janeiro.

## Como rodar o projeto localmente

Siga os passos abaixo na ordem para configurar o ambiente e iniciar a aplicação.

Recomendo que utilize um venv.

**1. Crie e ative um ambiente virtual (Recomendado)**
Crie um ambiente virtual (venv) antes de instalar as dependências do projeto.

No Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

No Linux / macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

**2. Instale as dependências**
Abra o terminal na raiz do projeto e instale as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

**3. Gere a base de dados (NECESSÁRIO)**
No mesmo terminal gere o arquivo csv executando o script:
```bash
python data_prep.py
```


**4. Rode a aplicação**
No terminal com o ambiente virtual ativado (o venv) execute:
```bash
streamlit run app.py
```