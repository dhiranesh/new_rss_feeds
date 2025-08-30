from db import get_article_by_guid, init_db
from config import DATABASE
import sys

# Initialize database
init_db(DATABASE)

# Check what's actually in the database
guid = "https://www.themoscowtimes.com/2025/08/22/lavrov-says-no-meeting-planned-between-putin-and-zelensky-a90295"
item = get_article_by_guid(guid)

if item:
    print("Article found:")
    print(f"Title: {item.get('title')}")
    print(f"Link: {item.get('link')}")
    print(f"Content HTML exists: {bool(item.get('content_html'))}")
    if item.get('content_html'):
        print(f"Content preview: {item.get('content_html')[:200]}...")
    else:
        print("Content HTML is empty/None")
else:
    print("Article not found in database")
