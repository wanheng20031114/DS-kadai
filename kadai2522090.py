import requests
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse
from collections import deque
import json
import time

# 開始URL
START_URL = "https://www.musashino-u.ac.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MusashinoCrawler/1.0)"}
TIMEOUT = 10  # 秒
SLEEP = 0.5   # リクエスト間隔
MAX_PAGES = 30  # 最大ページ数（課題提出用に制限）

def extract_links(html, base_url):
    """HTMLからコメントアウトされていない<a>タグのリンクを取得"""
    soup = BeautifulSoup(html, "html.parser")

    # コメントを削除
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        # javascript:, mailto:, tel:, # は無視
        if href.startswith(("javascript:", "mailto:", "tel:", "#")):
            continue
        full_url = urljoin(base_url, href)
        links.add(full_url)
    return links

def extract_title(html):
    """HTMLから<title>タグの文字列を取得"""
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    return title_tag.get_text(strip=True) if title_tag else ""

def crawl(start_url):
    """トップページから同一ドメインのリンクを辿り、タイトルを収集"""
    base_domain = urlparse(start_url).netloc
    visited = set()
    result = {}
    queue = deque([start_url])

    while queue and len(visited) < MAX_PAGES:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        print(f"クロール中: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            resp.encoding = 'utf-8'  # 強制UTF-8
            if resp.status_code != 200 or "text/html" not in resp.headers.get("Content-Type", ""):
                result[url] = ""
                continue
        except Exception as e:
            print(f"取得失敗: {url} ({e})")
            result[url] = ""
            continue

        html = resp.text
        # タイトルを抽出して辞書に保存
        title = extract_title(html)
        result[url] = title

        # ページ内の同一ドメインリンクを取得してキューに追加
        links = extract_links(html, url)
        for link in links:
            parsed = urlparse(link)
            normalized = parsed._replace(fragment="").geturl()
            if normalized not in visited and parsed.netloc == base_domain:
                queue.append(normalized)

        time.sleep(SLEEP)  # サーバーへの負荷軽減

    return result

def main():
    """メイン処理"""
    print(f"クロール開始: {START_URL}")
    data = crawl(START_URL)

    # URL順にソートして表示
    ordered = {k: data[k] for k in sorted(data.keys())}
    print("\n=== 辞書型変数 ===")
    print(ordered)

    # JSONとして保存（任意）
    with open("musashino_titles.json", "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)
    print("\nmusashino_titles.json に保存完了")

if __name__ == "__main__":
    main()
