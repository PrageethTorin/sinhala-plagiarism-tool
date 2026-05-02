import backend.writingstyleanalaysis.modules.web_scraper as ws

print("IMPORTING FROM:", ws.__file__)

url = "https://www.bbc.com/sinhala"
text = ws.scrape_url_content(url)

print("Extracted length:", len(text))
print(text[:500])