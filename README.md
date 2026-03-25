# AnimeDash

Dashboard interativo dos top 500 animes da [AniList](https://anilist.co), com sistema de recomendação baseado em similaridade de gêneros e tags.

## Funcionalidades

- **Inicio** — estatísticas gerais, scatter nota × popularidade, distribuição por status
- **Ranking** — top animes ordenados por nota ou popularidade, com capas e paginação
- **Graficos** — análises por gênero, estúdio e ano/temporada (barras, pizza, heatmap)
- **Busca** — busca por nome (romaji ou japonês) com cards detalhados
- **Recomendacoes** — sistema de recomendação por cosine similarity (gêneros + tags ponderadas)

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3.12 | Linguagem principal |
| Streamlit | Dashboard web |
| Plotly | Gráficos interativos |
| SQL Server | Banco de dados |
| pyodbc | Conexão com SQL Server |
| pandas / numpy | Manipulação de dados |
| requests | Chamadas à AniList GraphQL API |

## Pré-requisitos

- Python 3.10+
- SQL Server (local) com autenticação Windows
- ODBC Driver 17 ou 18 for SQL Server — [download](https://learn.microsoft.com/pt-br/sql/connect/odbc/download-odbc-driver-for-sql-server)

## Instalação e execução

```bash
# 1. Clonar o repositório
git clone https://github.com/guiharaujo/AnimeDash.git
cd AnimeDash

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar o banco de dados (apenas na primeira vez)
sqlcmd -S localhost -No -i database/schema.sql

# 4. Popular o banco com os top 500 animes (~2 minutos)
python run_etl.py

# 5. Iniciar o dashboard
streamlit run app/main.py --server.headless true
```

Acesse em: **http://localhost:8501**

## Estrutura do projeto

```
AnimeDash/
├── run_etl.py              # Entry point do ETL
├── requirements.txt
├── database/
│   ├── connection.py       # Conexão pyodbc (auto-detecta driver)
│   ├── schema.sql          # Criação das tabelas
│   └── repository.py       # Funções de leitura e escrita
├── api/
│   ├── anilist_client.py   # Cliente GraphQL com retry
│   └── queries.py          # Queries GraphQL
├── etl/
│   ├── fetcher.py          # Busca 500 animes (10 páginas)
│   ├── transformer.py      # Transforma API → banco
│   └── loader.py           # Salva no SQL Server
├── recommendation/
│   └── engine.py           # Algoritmo de recomendação
└── app/
    └── main.py             # Dashboard Streamlit completo
```

## Banco de dados

**Connection string:**
```
Server=localhost;Database=AnimeDash;Trusted_Connection=yes;TrustServerCertificate=yes;
```

**Tabelas:**

| Tabela | Campos |
|---|---|
| Animes | id, titulo, titulo_original, generos, nota, popularidade, episodios, status, temporada, ano, estudio, descricao, capa_url |
| Tags | id, nome, descricao |
| Anime_Tags | id_anime, id_tag, rank |

## Como atualizar e subir para o GitHub

**Toda alteração no projeto deve ser enviada ao GitHub:**

```bash
git add .
git commit -m "descrição da alteração"
git push origin main
```

O repositório está em: https://github.com/guiharaujo/AnimeDash

## ETL — Atualizar os dados

Para atualizar os dados com os animes mais recentes da AniList:

```bash
python run_etl.py
```

O ETL é **idempotente** — pode ser re-executado sem duplicar dados (usa MERGE upsert).

## Sistema de recomendação

O algoritmo usa **cosine similarity ponderada**:

1. Cada anime é representado por um vetor de features
2. Gêneros têm peso **1.0** (binário)
3. Tags têm peso proporcional ao **rank de relevância** (0–100) fornecido pela AniList
4. A similaridade é calculada como: `sim(A,B) = dot(A,B) / (||A|| × ||B||)`
5. Os 10 animes com maior similaridade são retornados

## Fonte dos dados

Dados fornecidos pela [AniList GraphQL API](https://graphql.anilist.co) — gratuita, sem necessidade de chave de API.
