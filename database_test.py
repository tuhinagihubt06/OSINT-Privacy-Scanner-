import sqlite3

connection = sqlite3.connect("scan_history.db")

cursor = connection.cursor()

cursor.execute('''
                   SELECT risk, COUNT(*) FROM scan_history
                   GROUP BY risk
                   ''')

records = cursor.fetchall()
for risk, count in records:
    print(f"Risk: {risk}: {count}")

connection.close()