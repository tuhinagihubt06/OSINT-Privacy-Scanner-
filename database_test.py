import sqlite3

connection = sqlite3.connect("scan_history.db")

cursor = connection.cursor()

cursor.execute("SELECT * FROM scan_history")
records = cursor.fetchall()
print("Database records: ", records)

connection.close()