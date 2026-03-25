# AnimeDash — Guia para o Claude

## O que é este projeto

Dashboard interativo de animes construído em Python. Busca os top 500 animes da AniList API (GraphQL), armazena em SQL Server e exibe em um dashboard Streamlit com sistema de recomendação por cosine similarity.

## Estrutura do projeto

```
Animes/
├── run_etl.py                  # Script para buscar dados da API e salvar no banco
├── requirements.txt
├── database/
│   ├── connection.py           # Conexão pyodbc (auto-detecta driver ODBC 17/18)
│   ├── schema.sql              # DDL das 3 tabelas: Animes, Tags, Anime_Tags
│   └── repository.py          # Funções de leitura/escrita (MERGE upserts)
├── api/
│   ├── anilist_client.py       # Cliente GraphQL com retry no rate-limit 429
│   └── queries.py              # Query GraphQL com todos os campos necessários
├── etl/
│   ├── fetcher.py              # Busca 10 páginas (50/pág = 500 animes)
│   ├── transformer.py          # Mapeia raw API → schema do banco
│   └── loader.py               # Executa MERGE upserts no SQL Server
├── recommendation/
│   └── engine.py               # Cosine similarity (gêneros + tags ponderadas por rank)
└── app/
    └── main.py                 # App Streamlit completo (arquivo único)
```

## Tecnologias

- **Python 3.12**
- **Streamlit 1.55** — dashboard web
- **Plotly 6** — gráficos interativos
- **pyodbc** — conexão com SQL Server
- **pandas / numpy** — manipulação de dados
- **requests** — chamadas à AniList API

## Banco de dados

- **SQL Server local** — banco `AnimeDash`
- Connection string: `Server=localhost;Database=AnimeDash;Trusted_Connection=yes;TrustServerCertificate=yes;`
- Tabelas: `Animes`, `Tags`, `Anime_Tags`
- Inicializar schema: `sqlcmd -S localhost -No -i database/schema.sql`

## Como rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Criar banco (apenas na primeira vez)
sqlcmd -S localhost -No -i database/schema.sql

# 3. Popular banco com 500 animes (leva ~2 minutos)
python run_etl.py

# 4. Iniciar dashboard
streamlit run app/main.py --server.headless true
```

## Regras de desenvolvimento

### OBRIGATORIO: Subir para o GitHub após qualquer alteração

Toda alteração no projeto DEVE ser commitada e enviada ao repositório GitHub:

```bash
git add .
git commit -m "descrição da alteração"
git push origin main
```

Repositório: https://github.com/guiharaujo/AnimeDash

### Não quebre estas coisas

- `app/main.py` é um arquivo único — não dividir em múltiplos arquivos de página sem garantir que os imports funcionem corretamente no Windows com Streamlit
- `repository.py` usa cursor direto (não `pd.read_sql`) por incompatibilidade com pandas 2.x + pyodbc
- O ETL é idempotente — pode ser re-executado sem duplicar dados (usa MERGE upsert)
- `get_connection()` em `database/connection.py` auto-detecta o driver ODBC — não hardcodar o nome do driver

### Padrões do código

- Sem emojis nos `st.title()` / `st.header()` — causa encoding issues no Windows com Python 3.12
- Textos de print no ETL sem caracteres especiais (→, ✓, etc.) — mesma razão
- Queries SQL com `?` como placeholder (padrão pyodbc)
- DataFrames carregados via cursor: `pd.DataFrame.from_records(rows, columns=cols)`

## Páginas do dashboard

| Página | Descrição |
|---|---|
| Inicio | Métricas gerais + scatter nota×popularidade + distribuição por status |
| Ranking | Tabela com capa, barra de progresso na nota, paginação de 50 em 50 |
| Graficos | 3 abas: gêneros (barras + pizza), estúdios (bubble), ano/temporada (heatmap) |
| Busca | Busca por nome (título ou título original) com cards expandíveis |
| Recomendacoes | Cosine similarity em matriz gênero+tags → 10 animes similares |

## Sistema de recomendação

Algoritmo implementado inline em `app/main.py` (página Recomendacoes):
1. Busca o anime pelo nome (usa o de maior popularidade se múltiplos resultados)
2. Constrói matriz de features: gêneros (peso=1.0) + tags (peso=rank/100)
3. Cosine similarity: `sim = dot(A,B) / (|A| × |B|)` com numpy
4. Retorna top 10 mais similares com % de similaridade

## AniList API

- URL: `https://graphql.anilist.co`
- Gratuita, sem chave de API
- Limite: 50 resultados por página, ~90 req/min
- O cliente em `api/anilist_client.py` tem retry automático no HTTP 429
