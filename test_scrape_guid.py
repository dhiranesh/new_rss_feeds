import unittest
from fetcher import extract_article_content

class TestScrapeGuidContent(unittest.TestCase):
    def test_extract_article_content(self):
        # Example GUID (URL) from your dataset
        guid = "https://www.themoscowtimes.com/2025/08/21/what-stands-in-the-way-of-a-putin-zelensky-meeting-a90286"
        result = extract_article_content(guid)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("content_html"), "No content_html scraped!")
        print("Scraped content (truncated):", result["content_html"][:200])

if __name__ == "__main__":
    unittest.main()
