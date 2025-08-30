import requests
from bs4 import BeautifulSoup
import json
import datetime

# Replace with the correct GUID News URL
URL = "https://www.theguidenews.com/latest-news"  

def scrape_guid_news():
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.content, "lxml")

    news_list = []
    articles = soup.find_all("div", class_="news-card")  # Adjust class based on HTML structure

    for article in articles:
        try:
            title = article.find("h2").get_text(strip=True)
            link = article.find("a")["href"]
            image_tag = article.find("img")
            image = image_tag["src"] if image_tag else None
            summary = article.find("p").get_text(strip=True)
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            news_list.append({
                "title": title,
                "link": link,
                "image": image,
                "summary": summary,
                "date": date
            })
        except Exception as e:
            print(f"Skipping one article due to error: {e}")
            continue

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(news_list, f, indent=4, ensure_ascii=False)

    print(f"[+] Scraped {len(news_list)} news articles successfully!")

if __name__ == "__main__":
    scrape_guid_news()
