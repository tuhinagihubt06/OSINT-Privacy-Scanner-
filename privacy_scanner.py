import os 
from datetime import datetime
import requests 
import sqlite3


DB_PATH = "scan_history.db"
TXT_PATH = "scan_history.txt"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

platforms = {
    "GitHub": {"url": "https://github.com/{u}", "mode": "status"},
    "Twitter": {"url": "https://twitter.com/{u}", "mode": "status"}, #Twitter blocks unauthenticated scraping, so we use the standard Twitter URL
    "Instagram": {"url": "https://instagram.com/{u}", "mode": "status"},
    "LinkedIn": {"url": "https://linkedin.com/in/{u}", "mode": "status"},
    "Facebook": {"url": "https://facebook.com/{u}", "mode": "status"},
    "Reddit": {"url": "https://reddit.com/user/{u}", "mode": "status"},
    "Pinterest": {"url": "https://pinterest.com/{u}", "mode": "status"},
    "Medium": {"url": "https://medium.com/@{u}", "mode": "status"}
}

score_per_hit = 25
max_score = len(platforms) * score_per_hit




#------Initializing database------#

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        username TEXT,
        score INTEGER,
        risk TEXT
    )
''')
    conn.commit()
    conn.close() 
    
#------platform existence check------#

def check_platform(session, name, config, username):
    url = config["url"].format(u=username)
    mode = config["mode"]

    try:
        response = session.get(url, timeout=3, headers=headers, allow_redirects=True)

        if mode == "status":
            exists = response.status_code == 200

        elif mode == "status_no_redirect_404":
            final_url = response.url.rstrip("/")
            exists = (
                response.status_code == 200
                and username.lower() in final_url.lower()
            )

        elif mode == "json_reddit":
            exists = False
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "name" in data["data"]:
                    exists = data["data"]["name"].lower() == username.lower()

        else:
            print(f"Unknown mode '{mode}' for platform '{name}'")
            exists = False

        return exists, f"HTTP {response.status_code}"   # <-- always a tuple

    except Exception as e:
        print(f"Error checking {name}: {e}")
        return False, f"Request failed: {e}"             # <-- tuple here too
        
    
def scan_platforms(username):
    result = []
    score = 0
    session = requests.Session()
    
    for platform, config in platforms.items():
        exists, detail = check_platform(session, platform, config, username)
        result.append((platform, exists, detail))
        if exists:
            print(f"Username '{username}' exists on {platform}.")
            score += score_per_hit
            print(f"Current Score: {score}")
        else:
            print(f"Username '{username}' does not exist on {platform}.")
    
    return score, result

def calculate_risk(score):
    if score >= max_score * 0.6:
        return "High"
    elif score >= max_score * 0.35:
        return "Moderate"
    else:
        return "Low"
    
Recommendations = {
    "High": [
        "Consider changing your password immediately.",
        "Review your privacy settings on all platforms."
    ],
    "Moderate": [
        "Be cautious about the information you share online.",
        "Regularly update your security settings."
    ],
    "Low": [
        "Continue to practice good online hygiene.",
        "Stay informed about the latest security threats."
    ]
}

#------Persistence------#

def save_scan_history(username, score, risk):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to text file
    with open(TXT_PATH, "a", encoding="utf-8") as file:
        file.write(
            f"[{timestamp}] Username: {username} | "
            f"Exposure Score: {score} | "
            f"Risk Level: {risk}\n"
        )
        
    # Save to SQLite database
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO scan_history (timestamp, username, score, risk)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, username, score, risk))
    connection.commit()
    connection.close()
    
def view_scan_history():
    if not os.path.exists(TXT_PATH):
        print("No scan history available.")
        return

    with open(TXT_PATH, "r", encoding="utf-8") as file:
        content = file.read().strip()
        if not content:
            print("No scan history available.")
            return
        print("=== SCAN HISTORY ===")
        print(content)


def view_database_history(limit=10):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT username, score, risk, timestamp
        FROM scan_history
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    
    records = cursor.fetchall()
    if records:
        print("=== LATEST SCAN HISTORY FROM DATABASE ===")
        for record in records:
            print(f"Username: {record[0]} | Score: {record[1]} | Risk: {record[2]} | Timestamp: {record[3]}")
    else:
        print("No scan history found in the database.")
        return
    print(f"Latest {len(records)} scan(s) displayed: ")
    for username, score, risk, timestamp in records:
        print(f"Username: {username} | Score: {score}/100 | Risk: {risk} | Timestamp: {timestamp}")
    connection.close()
    
def search_username_history(username):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    cursor.execute('''
        SELECT username, score, risk, timestamp
        FROM scan_history
        WHERE username = ?
        ORDER BY timestamp DESC
    ''', (username,))
    
    records = cursor.fetchall()
    if not records:
        print(f"No scan history found for '{username}'.")
        return
    print(f"Scan history for {username}:")
    for username, score, risk, timestamp in records:
        print(f"Username: {username} | Score: {score}/100 | Risk: {risk} | Timestamp: {timestamp}")
    connection.close()
    
    
def view_statistics():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    
    print("=== DATABASE STATISTICS ===")
    
    cursor.execute('SELECT COUNT(*) FROM scan_history')
    total_scans = cursor.fetchone()[0]
    print(f"Total Scans: {total_scans}")
    
    cursor.execute('''
                   SELECT risk, COUNT(*) FROM scan_history
                   GROUP BY risk
                   ''')

    records = cursor.fetchall()
    print("Risk Breakdown:")
    
    for risk, count in records:
        print(f"{risk or '<No Risk Level Assigned>'}: {count}")
    
    cursor.execute('''
                   SELECT username, COUNT(*) as scan_count
                     FROM scan_history
                     GROUP BY username
                     ORDER BY scan_count DESC
                     LIMIT 1
                     ''')
    top_users = cursor.fetchone()
    if top_users:
        print(f"Most frequently scanned username: {top_users[0]} ({top_users[1]} times)")
    connection.close()

#-----CLI Flow------#

def prompt_user_input(question):
    return input(question).strip().lower()=='yes'


def main():
    init_db()

    while True:
        print("\n=== Privacy Scanner ===")
        print("1. Scan a username")
        print("2. View scan history (text file)")
        print("3. View scan history (database)")
        print("4. Search scan history by username")
        print("5. View statistics")
        print("6. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            username = input("Enter the username to scan: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue                          # go back to menu, don't exit
            score, results = scan_platforms(username)
            for platform, exists, detail in results:
                if exists:
                    print(f"  [FOUND]     {platform}")
                else:
                    print(f"  [not found] {platform} ({detail})")
            risk = calculate_risk(score)
            save_scan_history(username, score, risk)
            print(f"\nExposure Score: {score} | Risk Level: {risk}")
            print(Recommendations[risk])

        elif choice == "2":
            view_scan_history()

        elif choice == "3":
            view_database_history()

        elif choice == "4":
            username = input("Enter the username to search: ").strip()
            search_username_history(username)

        elif choice == "5":
            view_statistics()

        elif choice == "6":
            print("Exiting Privacy Scanner.")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()