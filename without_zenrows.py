import requests

r = requests.get("https://www.scrapingcourse.com/antibot-challenge")
print(r.status_code, len(r.text))
