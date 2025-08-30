from flask import Flask, render_template, abort, jsonify, request, redirect, url_for, session, flash
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import traceback

from config import RSS_URL, APP_TITLE, APP_SOURCE_NAME, FETCH_INTERVAL_MINUTES, DATABASE, TIMEZONE
from db import init_db, upsert_article, get_latest, get_article_by_guid
from fetcher import parse_rss, extract_article_content, iso_dt

import json
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure random value

# Ensure DB is initialized for all environments (including production)
init_db(DATABASE)

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def load_users():
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    return data.get('users', [])

def check_user(username, password):
    users = load_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if check_user(username, password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', app_title=APP_TITLE)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

def fetch_and_update():
    """
    1) Parse RSS
    2) For each item, fetch full article page
    3) Upsert into SQLite keyed by GUID
    """
    try:
        feed = parse_rss(RSS_URL)
        for entry in feed.entries:
            guid = entry.get("id") or entry.get("guid") or entry.get("link")
            if not guid:
                continue
            link = entry.get("link")
            title = entry.get("title", "").strip()
            summary = (entry.get("summary") or entry.get("description") or "").strip()
            published = iso_dt(entry.get("published"))

            # Get the full content
            full = extract_article_content(link) if link else {"content_html": None, "top_image": None, "title": None}
            content_html = full["content_html"] or f"<p>{summary}</p>"
            top_image = full.get("top_image")

            # Prefer the page short title if available
            if full.get("title") and len(full["title"]) > len(title) - 8:
                title = full["title"]

            art = {
                "guid": guid,
                "title": title,
                "link": link,
                "summary": summary,
                "published": published,
                "content_html": content_html,
                "top_image": top_image
            }
            upsert_article(art)

        print(f"[{datetime.now()}] Fetched & updated.")
    except Exception as e:
        print("Fetch error:", e)
        traceback.print_exc()

# Fetch news immediately at startup (after definition)
fetch_and_update()

# Fetch news immediately at startup
fetch_and_update()

@app.route("/")
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    items = get_latest(30)
    return render_template("index.html",
                           items=items,
                           app_title=APP_TITLE,
                           source_name=APP_SOURCE_NAME,
                           username=session.get('username'))

@app.route("/article/<path:guid>")
def article_page(guid):
    item = get_article_by_guid(guid)
    if not item:
        abort(404)
    # If content_html is missing, fetch and update it automatically
    if not item.get("content_html") and item.get("link"):
        full = extract_article_content(item["link"])
        item["content_html"] = full["content_html"]
        item["top_image"] = full.get("top_image")
        # Optionally update the title if available
        if full.get("title") and len(full["title"]) > len(item["title"]) - 8:
            item["title"] = full["title"]
        upsert_article(item)
    return render_template("article.html",
                           item=item,
                           app_title=APP_TITLE,
                           source_name=APP_SOURCE_NAME)

@app.route("/api/article/<path:guid>")
def api_article(guid):
    item = get_article_by_guid(guid)
    if not item:
        return jsonify({"error": "not found"}), 404
    return jsonify(item)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(fetch_and_update, "interval", minutes=FETCH_INTERVAL_MINUTES, id="fetch_job", max_instances=1, coalesce=True)
    scheduler.start()
    # Make an immediate first run
    fetch_and_update()


if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=5000, debug=True)
