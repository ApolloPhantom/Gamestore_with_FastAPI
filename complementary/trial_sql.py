import sqlite3
import os.path

base = os.path.dirname(os.path.abspath(__file__))
db = "project.db"
db_path = os.path.join(base,db)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("select id from users where id = ?",("Admin",))
conn.close()