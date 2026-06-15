import requests
username = input("Enter a username to scan: ")
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
            score+=40
        else:
            print(f"Username '{username}' does not exist on {platform}.")
            
    except Exception as e:
        print(f"Error checking {platform}: Error")
        print(f"Error details: {e}")
print(f"Exposure Score: {score}/100")
print(f"Total score for username '{username}': {score}")

if score>=75:
    print("High exposure risk: The username is widely used across multiple platforms.")
elif score>=50:
    print("Moderate exposure risk: The username is used on several platforms.")
else:
    print("Low exposure risk: The username is not widely used across platforms.")