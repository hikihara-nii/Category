"""
comprehensive_provenance_server.py
==================================
多層的データ集積 (t=0 -> t=40) から最終論文に至る全ルーツ完全遡及・動的追跡Webサーバー
"""
import http.server
import socketserver
import webbrowser
import threading
import os

PORT = 8090
HTML_FILE = "comprehensive_provenance_explorer.html"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if os.path.exists(HTML_FILE):
            with open(HTML_FILE, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "HTML file not found")

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print("================================================================")
        print(f"[*] 多層的プロバナンス・完全遡及エクスプローラー起動")
        print(f"[*] URL: http://localhost:{PORT}")
        print("[*] 終了するにはターミナルで Ctrl+C を押してください")
        print("================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] サーバーを停止しました。")
            httpd.server_close()

if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    start_server()
