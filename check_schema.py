import sqlite3
conn = sqlite3.connect('uni_platform.db')
conn.row_factory = sqlite3.Row
for t in ['uni_cli', 'uni_vendor', 'uni_buy']:
    print(f"--- {t} ---")
    cursor = conn.execute(f"PRAGMA table_info({t})")
    for row in cursor:
        print(dict(row))
conn.close()
