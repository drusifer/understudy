"""Write a stage's decisions into the run database, where the SQL models read them."""


def store(connection, table: str, columns: dict[str, str], rows: list[dict]) -> None:
    """Replace `table` with `rows`; `columns` maps each column name to its DuckDB type."""
    connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.execute(f"CREATE TABLE {table} ({', '.join(f'{name} {kind}' for name, kind in columns.items())})")
    if rows:
        marks = ", ".join("?" for _ in columns)
        connection.executemany(f"INSERT INTO {table} VALUES ({marks})", [[row[name] for name in columns] for row in rows])
