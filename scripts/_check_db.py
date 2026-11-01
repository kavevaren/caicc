import sqlite3

c = sqlite3.connect(r"C:\tmp\orvina-p1\orvina.db")
print("schema_version:", list(c.execute("SELECT version FROM schema_version")))
n_tables = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
n_fts = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE name LIKE '%fts%' OR name LIKE '%idx_%' OR name LIKE 'trg_%'")]
print("tables (incl. shadows):", n_tables)
print("fts/idx/trg objects:", len(n_fts))
