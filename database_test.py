import sqlite3

connection = sqlite3.connect("scan_history.db")

cursor = connection.cursor()

cursor.execute('''SELECT * FROM scan_history
               WHERE timestamp >= '2023-01-01' ''')
records = cursor.fetchall()
print("Database records: ", records)

connection.close()