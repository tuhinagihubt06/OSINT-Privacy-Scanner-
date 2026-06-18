import os 
from datetime import datetime
import requests 
import sqlite3

username = input("Enter a username to scan: ")

# Initialize SQLite database
conn = sqlite3.connect("scan_history.db")
cursor = conn.cursor()

# Create table if it doesn't exist
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

def save_scan_history(username, score, risklevel):
    print("DEBUG: Entered save_scan_history")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #save to text file
    with open("scan_history.txt", "a", encoding = "utf-8") as file:
        file.write(
            f"[{timestamp}] Username: {username} |" 
            f"Exposure Score: {score} |"
            f"Risk Level: {risk}\n"
        )
        
    #save to SQLite database
    connection = sqlite3.connect("scan_history.db")
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO scan_history (timestamp, username, score, risk)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, username, score, risk))
    connection.commit()
    connection.close()
    
    print("Scan history saved to database.")
        
    print("DEBUG: File write completed")
    print(f"SAVE PATH: {os.path.abspath('scan_history.txt')}")

def view_scan_history():
    try:
        with open("scan_history.txt", "r", encoding = "utf-8") as file:
            history = file.read()
            
        print(f"DEBUG: history = {repr(history)}")
        if history.strip():
            print("\nScan History:")
            print(history)
        else:
            print(f"DEBUG: File exists but is empty.")
            
    except FileNotFoundError:
        print("DEBUG: File not found. No scan history available.")
    
    print(f"VIEW PATH: {os.path.abspath('scan_history.txt')}")

        
        


platforms = {
    "GitHub": f"https://github.com/{username}",
    "Twitter": f"https://twitter.com/{username}",
    "Instagram": f"https://instagram.com/{username}",
    "LinkedIn": f"https://linkedin.com/in/{username}",
    "Facebook": f"https://facebook.com/{username}",
    "Reddit": f"https://reddit.com/user/{username}",
    "Pinterest": f"https://pinterest.com/{username}",
    "Medium": f"https://medium.com/@{username}"
}
score = 0
for platform, url in platforms.items():
    try:
        response = requests.get(url, timeout=3)
    
        if response.status_code == 200:
            print(f"Username '{username}' exists on {platform}.")
            score+=25
            print(f"Current Score: {score}")
            
        else:
            print(f"Username '{username}' does not exist on {platform}.")
            
            
    except Exception as e:
        print(f"Error checking {platform}: Error")
        print(f"Error details: {e}")
        
print(f"Exposure Score: {score}/200")
print(f"Total score for username '{username}': {score}")    
if score>=75:
    risk = "High"
    print("High exposure risk: The username is widely used across multiple platforms.")
elif score>=50:
    risk = "Moderate"
    print("Moderate exposure risk: The username is used on several platforms.")
else:
    risk = "Low"
    print("Low exposure risk: The username is not widely used across platforms.")
    
        
if risk == "High":
    print('''Recommendation: Consider changing your username to reduce exposure risk.
          - Use a unique username that is not easily guessable.
          - Remove personal information from your username, such as your real name or birthdate.
          - Regularly review and update your online profiles to ensure they do not contain sensitive information.
          - Use different usernames for different platforms to minimize the risk of cross-platform exposure.''')

elif risk == "Moderate":
    print('''Recommendation: Be cautious with your username and consider the following:
          - Review profile visibility changes.
          - Check linked accounts for any security vulnerabilities.
          - Consider changing your username if it contains personal information or is easily guessable.''')

else:
    print('''Recommendation: Your username has a low exposure risk, but it's still important to:
          - Regularly review your online profiles for any sensitive information.
          - Use strong, unique passwords for each platform.
          - Enable two-factor authentication where available to enhance account security.''')
    
save_scan_history(username, score, risk)
print("Scan history saved.")

view_history = input("Do you want to view your scan history? (yes/no): ").strip().lower()
if view_history == "yes":
    view_scan_history()
else:    
    print("Scan history not displayed.")
    
