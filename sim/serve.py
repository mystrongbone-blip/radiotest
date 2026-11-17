#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
骨骼 3D 檢視器 本機啟動器

用法：
    python serve.py                 用 8000，自動開瀏覽器
    python serve.py 8080            指定埠
    python serve.py 8080 --no-open  不自動開瀏覽器
    python serve.py --lan           綁 0.0.0.0，可用手機／平板連進來
    python serve.py --list          只檢查檔案，不起伺服器
"""

import os
import sys
import socket
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))

# .glb 若用系統預設 MIME，GLTFLoader 會因為 content-type 不對而報錯，這裡強制指定
EXTRA_TYPES = {
    '.glb':  'model/gltf-binary',
    '.gltf': 'model/gltf+json',
    '.bin':  'application/octet-stream',
    '.wasm': 'application/wasm',
    '.js':   'text/javascript',
    '.mjs':  'text/javascript',
    '.json': 'application/json',
    '.hdr':  'image/vnd.radiance',
    '.exr':  'image/x-exr',
    '.ktx2': 'image/ktx2',
}

ENTRY_HINTS = ['viewer.html', 'index.html', 'skeleton.html', '骨骼3D.html']


# ------------------------------------------------------------------ 工具
def find_entry():
    """找根目錄的 html。優先序：常見檔名 > 只有一個 html > 第一個 html。"""
    htmls = sorted(
        f for f in os.listdir(ROOT)
        if f.lower().endswith(('.html', '.htm')) and os.path.isfile(os.path.join(ROOT, f))
    )
    if not htmls:
        return None
    for name in ENTRY_HINTS:
        if name in htmls:
            return name
    return htmls[0]


def find_glb():
    """列出可用的 glb，讓啟動時就知道會不會載到東西。"""
    hits = []
    for rel in ('build/skeleton_fixed.glb', 'skeleton_fixed.glb',
                'build/skeleton.glb', 'skeleton.glb'):
        p = os.path.join(ROOT, rel.replace('/', os.sep))
        if os.path.isfile(p):
            hits.append((rel, os.path.getsize(p)))
    return hits


def port_free(port, host):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def pick_port(start, host, span=30):
    for p in range(start, start + span):
        if port_free(p, host):
            return p
    return None


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or unit == 'GB':
            return ('%d %s' % (n, unit)) if unit == 'B' else ('%.1f %s' % (n, unit))
        n /= 1024.0


# ------------------------------------------------------------------ Handler
class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # 網址 / 自動導到入口 html
    def do_GET(self):
        if self.path in ('/', '/index.html') and ENTRY:
            self.path = '/' + ENTRY
        super().do_GET()

    # 本機開發關掉快取，改完 glb 或 html 重新整理就生效
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext in EXTRA_TYPES:
            return EXTRA_TYPES[ext]
        return super().guess_type(path)

    # 只印錯誤與 .glb，避免 console 被一堆圖片請求洗掉
    def log_message(self, fmt, *args):
        try:
            status = str(args[1])
        except IndexError:
            status = ''
        low = self.path.lower()
        if status.startswith(('4', '5')):
            print('   [!] %s  %s' % (self.path, status))
        elif low.endswith(('.glb', '.gltf', '.html')):
            print('   [ok] %s  %s' % (self.path, status))


# ------------------------------------------------------------------ 主程式
def main():
    global ENTRY

    argv = sys.argv[1:]
    flags = set(a.lower() for a in argv if a.startswith('--'))
    nums = [a for a in argv if not a.startswith('--')]
    start_port = int(nums[0]) if nums and nums[0].isdigit() else 8000
    use_lan = '--lan' in flags
    no_open = '--no-open' in flags
    list_only = '--list' in flags

    ENTRY = find_entry()
    glbs = find_glb()

    print()
    print('  骨骼 3D 檢視器 啟動器')
    print('  ' + '-' * 52)
    print('  工作資料夾  %s' % ROOT)
    print('  入口檔案    %s' % (ENTRY or '找不到 html'))
    if glbs:
        for rel, size in glbs:
            print('  模型        %s  (%s)' % (rel, human(size)))
    else:
        print('  模型        找不到 skeleton_fixed.glb')
    print('  ' + '-' * 52)

    if list_only:
        print()
        print('  Python %s' % sys.version.split()[0])
        print('  （--list 模式，未啟動伺服器）')
        print()
        return 0

    if not ENTRY:
        print()
        print('  [中止] 這個資料夾沒有 .html。')
        print('         請把 serve.py 放在跟 html 同一層再執行。')
        print()
        return 1

    host = '0.0.0.0' if use_lan else '127.0.0.1'
    port = pick_port(start_port, host)
    if port is None:
        print()
        print('  [中止] %d 到 %d 都被佔用了。' % (start_port, start_port + 29))
        print('         換一個：python serve.py 9000')
        print()
        return 1

    try:
        httpd = ThreadingHTTPServer((host, port), Handler)
    except OSError as e:
        print()
        print('  [中止] 無法綁定 %s:%d  %s' % (host, port, e))
        print()
        return 1

    httpd.daemon_threads = True

    local_url = 'http://localhost:%d/%s' % (port, ENTRY)
    print()
    print('  網址  http://localhost:%d' % port)
    if use_lan:
        print('  區網  http://%s:%d   （同一個 Wi-Fi 的平板／手機可用）' % (lan_ip(), port))
    print()
    print('  停止  Ctrl + C')
    print('  重新整理就會重新下載模型，改 glb 不必重開伺服器')
    print()

    if not no_open:
        threading.Timer(0.6, lambda: webbrowser.open(local_url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
        print('  收到 Ctrl+C，正在關閉…')
    finally:
        httpd.shutdown()
        httpd.server_close()
        print('  已停止。')
    return 0


if __name__ == '__main__':
    sys.exit(main())