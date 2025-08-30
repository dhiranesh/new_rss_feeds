from fetcher import extract_article_content
from db import init_db, upsert_article
from config import DATABASE

# Initialize database
init_db(DATABASE)

# Test scraping the specific article
guid = "https://www.themoscowtimes.com/2025/08/22/lavrov-says-no-meeting-planned-between-putin-and-zelensky-a90295"

print(f"Testing scraping: {guid}")
result = extract_article_content(guid)

print(f"Content extracted: {bool(result.get('content_html'))}")
if result.get('content_html'):
    print(f"Content preview: {result.get('content_html')[:300]}...")
    
    # Save to database
    article = {
        "guid": guid,
        "title": "Lavrov Says 'No Meeting Planned' Between Putin and Zelensky",
        "link": guid,
        "summary": "The foreign minister's remarks on Meet the Press were the latest and clearest indication that a Putin-Zelensky summit is nowhere on the horizon.",
        "published": "2025-08-22T13:33:00+00:00",
        "content_html": result.get('content_html'),
        "top_image": result.get('top_image')
    }
    upsert_article(article)
    print("Article saved to database!")
else:
    print("No content extracted")
