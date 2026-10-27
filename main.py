import csv
import html.parser
import re
import time
from urllib.parse import urljoin, urlparse
import urllib.request

START_URL = "https://www.musashino-u.ac.jp/"
TARGET_DOMAIN = urlparse(START_URL).netloc

sitemap = {}
visited_urls = set()
MAX_PAGES = 10  # テスト用にまずは10ページ取得


class SimpleHTMLParser(html.parser.HTMLParser):

    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.links = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "a":
            for attr, val in attrs:
                if attr == "href" and val:
                    full_url = urljoin(self.base_url, val)
                    parsed = urlparse(full_url)
                    clean_url = (
                        f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    )
                    if (
                        parsed.netloc == TARGET_DOMAIN
                        and parsed.scheme in ["http", "https"]
                    ):
                        self.links.append(clean_url)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()


def get_page_info(url):
    time.sleep(2)  # 負荷軽減（2秒待機）

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None, []

            html_text = response.read().decode("utf-8", errors="ignore")
            parser = SimpleHTMLParser(url)
            parser.feed(html_text)

            title = parser.title if parser.title else "No Title"
            return title, parser.links

    except Exception as e:
        print(f"エラー: {url} -> {e}")
        return None, []


def crawl(url):
    if url in visited_urls or len(sitemap) >= MAX_PAGES:
        return

    print(f"探索中 ({len(sitemap)+1}/{MAX_PAGES}): {url}")
    visited_urls.add(url)

    title, links = get_page_info(url)
    if title:
        sitemap[url] = title

    for link in links:
        if len(sitemap) >= MAX_PAGES:
            break
        if link not in visited_urls:
            crawl(link)


def save_to_csv(filename="sitemap.csv"):
    with open(filename, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title"])
        for url, title in sitemap.items():
            writer.writerow([url, title])


if __name__ == "__main__":
    print("スクレイピングを開始します...")
    crawl(START_URL)

    print("CSVファイルに保存します...")
    save_to_csv("sitemap.csv")
    print("完了しました！")