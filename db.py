import sqlite3
from contextlib import contextmanager

DB_PATH = None  # set by init_db

def init_db(db_path: str):
    global DB_PATH
    DB_PATH = db_path
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            guid TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            summary TEXT,
            published TEXT,
            content_html TEXT,
            top_image TEXT,
            last_fetched TEXT
        )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_published ON articles(published)")
        con.commit()

@contextmanager
def get_conn():
    con = sqlite3.connect(DB_PATH)
    try:
        yield con
    finally:
        con.close()

def upsert_article(article):
    with get_conn() as con:
        con.execute("""
        INSERT INTO articles (guid, title, link, summary, published, content_html, top_image, last_fetched)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(guid) DO UPDATE SET
            title=excluded.title,
            link=excluded.link,
            summary=excluded.summary,
            published=excluded.published,
            content_html=excluded.content_html,
            top_image=excluded.top_image,
            last_fetched=datetime('now')
        """, (
            article["guid"],
            article.get("title"),
            article.get("link"),
            article.get("summary"),
            article.get("published"),
            article.get("content_html"),
            article.get("top_image"),
        ))
        con.commit()

def get_latest(limit=30):
    with get_conn() as con:
        cur = con.execute("""
        SELECT guid, title, link, summary, published, top_image
        FROM articles
        ORDER BY datetime(published) DESC, rowid DESC
        LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
    cols = ["guid", "title", "link", "summary", "published", "top_image"]
    return [dict(zip(cols, r)) for r in rows]

def get_article_by_guid(guid: str):
    with get_conn() as con:
        cur = con.execute("""
        SELECT guid, title, link, summary, published, content_html, top_image, last_fetched
        FROM articles WHERE guid=?
        """, (guid,))
        row = cur.fetchone()
    if not row:
        return None
    cols = ["guid","title","link","summary","published","content_html","top_image","last_fetched"]
    return dict(zip(cols, row))

