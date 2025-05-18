import tkinter as tk
from tkinter import simpledialog, messagebox
import requests
from bs4 import BeautifulSoup
import re

class NormalBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("Normalブラウザ")
        self.history = []
        self.bookmarks = []
        self.current_url = None
        self.dark_mode = True
        self.dark_mode_level = 0.8  # 0(明るい)〜1(真っ黒)

        # メニュー
        menubar = tk.Menu(root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="ブックマークに追加", command=self.add_bookmark)
        filemenu.add_command(label="ブックマークを見る", command=self.show_bookmarks)
        menubar.add_cascade(label="ブックマーク", menu=filemenu)

        mode_menu = tk.Menu(menubar, tearoff=0)
        mode_menu.add_command(label="ダークモード切替", command=self.toggle_dark_mode)
        mode_menu.add_command(label="ダークモード濃さ変更", command=self.change_dark_mode_level)
        menubar.add_cascade(label="表示", menu=mode_menu)

        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="戻る", command=self.go_back)
        menubar.add_cascade(label="ナビゲーション", menu=nav_menu)

        root.config(menu=menubar)

        # 検索／URL入力欄
        self.input_entry = tk.Entry(root, font=("Arial", 14))
        self.input_entry.pack(fill="x")
        self.input_entry.bind("<Return>", lambda e: self.process_input(self.input_entry.get()))

        # ページ表示用テキスト
        self.text = tk.Text(root, wrap="word", font=("Arial", 12))
        self.text.pack(expand=True, fill="both")

        self.apply_dark_mode()

    def apply_dark_mode(self):
        if self.dark_mode:
            bg_val = int(255 * (1 - self.dark_mode_level))
            bg_color = f"#{bg_val:02x}{bg_val:02x}{bg_val:02x}"
            fg_color = "white"
        else:
            bg_color = "white"
            fg_color = "black"
        self.text.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.input_entry.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.root.config(bg=bg_color)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_dark_mode()

    def change_dark_mode_level(self):
        level = simpledialog.askfloat("ダークモード濃さ", "濃さを0.0(明るい)〜1.0(真っ黒)で指定:", minvalue=0.0, maxvalue=1.0)
        if level is not None:
            self.dark_mode_level = level
            if self.dark_mode:
                self.apply_dark_mode()

    def add_bookmark(self):
        if self.current_url:
            if self.current_url not in self.bookmarks:
                self.bookmarks.append(self.current_url)
                messagebox.showinfo("ブックマーク追加", "ブックマークに追加しました！")
            else:
                messagebox.showinfo("ブックマーク追加", "すでに追加済みです。")
        else:
            messagebox.showwarning("ブックマーク追加", "表示中のページがありません。")

    def show_bookmarks(self):
        if not self.bookmarks:
            messagebox.showinfo("ブックマーク", "ブックマークは空です。")
            return
        menu = tk.Toplevel(self.root)
        menu.title("ブックマーク一覧")
        listbox = tk.Listbox(menu, font=("Arial", 12))
        listbox.pack(fill="both", expand=True)
        for url in self.bookmarks:
            listbox.insert("end", url)

        def on_select(event):
            sel = listbox.curselection()
            if sel:
                url = listbox.get(sel[0])
                self.load_url(url)
                menu.destroy()

        listbox.bind("<Double-1>", on_select)

    def go_back(self):
        if len(self.history) >= 2:
            self.history.pop()  # 今のページを削除
            prev_url = self.history.pop()  # 一つ前のページ取得
            self.load_url(prev_url, add_history=False)
        else:
            messagebox.showinfo("戻る", "戻る履歴がありません。")

    def process_input(self, input_text):
        input_text = input_text.strip()
        if not input_text:
            return

        # URL判定(簡易)
        if input_text.startswith("http://") or input_text.startswith("https://"):
            self.load_url(input_text)
        elif re.match(r"^[\w\-]+\.[\w\-]+", input_text):  # ドメインっぽい文字列ならURLとして試す
            self.load_url("http://" + input_text)
        else:
            self.search_bing(input_text)

    def search_bing(self, query):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", f"『{query}』の検索結果を取得中…少々待ってね\n\n")

        search_url = "https://www.bing.com/search?q=" + requests.utils.quote(query)
        try:
            res = requests.get(search_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            results = []
            for item in soup.select('li.b_algo h2 a'):
                href = item.get('href')
                title = item.get_text()
                if href and title:
                    results.append((title, href))
                if len(results) >= 10:
                    break

            if not results:
                self.text.insert("end", "検索結果が見つかりませんでした。\n")
                return

            self.text.delete("1.0", "end")
            self.text.insert("1.0", f"『{query}』の検索結果:\n\n")
            for i, (title, href) in enumerate(results, 1):
                self.text.insert("end", f"[{i}] {title}\n{href}\n\n")

            # 選択待ちの入力ダイアログ
            def select_result():
                sel = simpledialog.askinteger("アクセス", "アクセスしたい番号を入力してください（キャンセルで中断）:", minvalue=1, maxvalue=len(results))
                if sel is None:
                    return
                title, url = results[sel - 1]
                self.load_url(url)

            # ちょっと遅延させて選択ダイアログ出す
            self.root.after(100, select_result)

        except Exception as e:
            self.text.insert("end", f"検索失敗: {e}\n")

    def load_url(self, url, add_history=True):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", f"{url} にアクセス中…少々待ってね\n")

        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            self.current_url = url
            if add_history:
                self.history.append(url)

            soup = BeautifulSoup(res.text, "html.parser")

            title = soup.title.string if soup.title else url

            texts = []
            for tag in soup.find_all(['h1', 'h2', 'h3', 'p']):
                txt = tag.get_text(strip=True)
                if txt:
                    texts.append(txt)

            display_text = f"=== {title} ===\n\n" + "\n\n".join(texts[:40])
            self.text.delete("1.0", "end")
            self.text.insert("1.0", display_text)

            self.input_entry.delete(0, "end")
            self.input_entry.insert(0, url)

        except Exception as e:
            messagebox.showerror("エラー", f"ページ取得失敗: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NormalBrowser(root)
    root.geometry("800x600")
    root.mainloop()