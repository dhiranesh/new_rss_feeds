import requests
import feedparser
from bs4 import BeautifulSoup
from readability import Document
from dateutil import parser as dateparser
from datetime import datetime, timezone
import time
from typing import Optional
from config import USER_AGENT
from urllib.parse import urljoin

def http_get(url, timeout=20):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }
    return requests.get(url, headers=headers, timeout=timeout)

def parse_rss(rss_url: str):
    # requests first for better headers + retries
    r = http_get(rss_url)
    r.raise_for_status()
    return feedparser.parse(r.content)

def iso_dt(s: Optional[str]) -> str:
    if not s:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = dateparser.parse(s)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def extract_article_content(url: str):
    """
    Fetch article page and extract readable HTML + a top image if possible.
    Uses readability + BeautifulSoup cleanup. Works for most publisher pages.
    """
    try:
        resp = http_get(url, timeout=25)
        resp.raise_for_status()
    except Exception:
        return {"content_html": None, "top_image": None, "title": None}

    html = resp.text
    content_html = None
    title = None
    # Try readability first
    try:
        doc = Document(html)
        content_html = doc.summary(html_partial=True)
        title = doc.short_title()
    except Exception:
        content_html = None
        title = None

    # Fallback: use BeautifulSoup to extract <article> or largest <div> with text
    if not content_html:
        soup = BeautifulSoup(html, "lxml")
        article_tag = soup.find("article")
        if article_tag:
            # Clean up unwanted elements
            for unwanted in article_tag.find_all(["script", "style", "nav", "header", "footer", "aside", "button", "form"]):
                unwanted.decompose()
            # Remove social media buttons and ads
            for unwanted in article_tag.find_all(class_=["share", "social", "btn", "button", "ad", "advertisement", "promo"]):
                unwanted.decompose()
            content_html = str(article_tag)
        else:
            # fallback: find the largest <div> with text
            divs = soup.find_all("div")
            largest = max(divs, key=lambda d: len(d.get_text(strip=True)), default=None)
            if largest and len(largest.get_text(strip=True)) > 200:
                # Clean up unwanted elements
                for unwanted in largest.find_all(["script", "style", "nav", "header", "footer", "aside", "button", "form"]):
                    unwanted.decompose()
                content_html = str(largest)
            else:
                # fallback: just use the body
                body = soup.find("body")
                if body:
                    content_html = str(body)

    # Try to find a good image
    top_image = None
    try:
        soup = BeautifulSoup(html, "lxml")
        og = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name":"og:image"})
        if og and og.get("content"):
            top_image = urljoin(url, og["content"])
        else:
            img = soup.find("article")
            img = img.find("img") if img else soup.find("img")
            if img and img.get("src"):
                top_image = urljoin(url, img["src"])
    except Exception:
        pass

    return {"content_html": content_html, "top_image": top_image, "title": title}

