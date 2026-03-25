import pyodbc


def get_driver() -> str:
    drivers = pyodbc.drivers()
    for preferred in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]:
        if preferred in drivers:
            return preferred
    # fallback: use any SQL Server driver found
    for d in drivers:
        if "SQL Server" in d:
            return d
    raise RuntimeError(
        "Nenhum driver ODBC para SQL Server encontrado. "
        "Instale o 'ODBC Driver 17 for SQL Server' ou superior."
    )


def get_connection() -> pyodbc.Connection:
    driver = get_driver()
    conn_str = (
        f"DRIVER={{{driver}}};"
        "Server=localhost;"
        "Database=AnimeDash;"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)
