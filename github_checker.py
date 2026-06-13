import requests 
Username = input("Enter a GitHub username: ")
url = f"https://github.com/{Username}"
response = requests.get(url)
if response.status_code == 200:
    print(f"Username '{Username}' exists on GitHub.")
else:
    print(f"Username '{Username}' does not exist on GitHub.")