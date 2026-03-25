"""
ETL entry point: busca os top 500 animes da AniList e salva no SQL Server.

Uso:
    python run_etl.py
"""
import sys
import os

# Garante que o diretório raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from etl.fetcher import fetch_all_animes
from etl.loader import load_all


def main():
    print("=" * 50)
    print("AnimeDash ETL")
    print("=" * 50)

    print("\n[1/2] Buscando animes na AniList API...")
    raw_animes = fetch_all_animes(total=500, per_page=50)
    print(f"\n> Total de animes buscados: {len(raw_animes)}")

    print("\n[2/2] Carregando dados no banco de dados SQL Server...")
    load_all(raw_animes)

    print("\nETL concluído com sucesso!")
    print("Execute: streamlit run app/main.py")


if __name__ == "__main__":
    main()
