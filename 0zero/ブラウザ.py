import requests
import re

def get_full_light_text(url, timeout=15):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        content = r.content.decode('utf-8', errors='ignore')

        # JSとCSSを全部削除
        content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)

        # HTMLタグを全部除去
        content = re.sub(r'<[^>]+>', '', content)

        # &#91;数字&#93; → 空文字に
        content = re.sub(r'&#91;\d+&#93;', '', content)

        # [数字] → 空文字に
        content = re.sub(r'\d+', '', content)

        # 空白を整理
        content = re.sub(r'\s+', ' ', content).strip()

        return content
    except Exception as e:
        return f"読み込みエラー: {e}"

def is_url(text):
    return text.startswith("http://") or text.startswith("https://")

def search_and_browse():
    base_search_url = "https://www.bing.com/search?q="

    while True:
        inp = input("検索ワードかURLを入力（終了はexit）: ").strip()
        if inp.lower() == "exit":
            print("終了！またね！")
            break

        if is_url(inp):
            urls = [inp]
        else:
            search_url = base_search_url + inp.replace(" ", "+")
            print(f"検索中… {search_url}")
            try:
                r = requests.get(search_url)
                r.raise_for_status()
                html = r.text
                links = re.findall(r'<a href="(https?://[^"]+)"', html)
                seen = set()
                urls = []
                for link in links:
                    if link not in seen and "bing.com" not in link:
                        seen.add(link)
                        urls.append(link)
                    if len(urls) >= 10:
                        break
                if not urls:
                    print("検索結果が見つかりませんでした。")
                    continue
            except Exception as e:
                print(f"検索失敗: {e}")
                continue

        for i, url in enumerate(urls, start=1):
            print(f"[{i}] {url}\n")

        while True:
            choice = input("アクセスしたいサイトの番号を入力（検索やexitで戻る）: ").strip()
            if choice.lower() in ["exit", "search"]:
                break
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(urls):
                    selected_url = urls[idx]
                    print(f"{selected_url} にアクセス中…")
                    text = get_full_light_text(selected_url)
                    print(text)  # ←全文表示に変更（5000文字制限を解除）
                    print("\n--- ページ表示終了 ---\n")
                else:
                    print("番号が範囲外です。もう一度入力してね。")
            else:
                print("数字で番号を入力してね！")

search_and_browse()