import os
import sys
import socket
import secrets
import hmac
import html
import threading
import traceback
import datetime
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import PySimpleGUI as sg


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _base_dir()
ERROR_LOG = os.path.join(BASE_DIR, "error_log.txt")


def _log_crash(exc_type, exc_value, exc_tb, title="Uncaught Exception"):
    try:
        with open(ERROR_LOG, "a", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write("[{}] {}\n".format(
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), title))
            f.write("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
            f.write("\n")
    except Exception:
        pass


def _excepthook(exc_type, exc_value, exc_tb):
    _log_crash(exc_type, exc_value, exc_tb, "Main Thread Uncaught Exception")


def _thread_excepthook(args):
    _log_crash(args.exc_type, args.exc_value, args.exc_traceback, "Sub-thread Exception")


sys.excepthook = _excepthook
threading.excepthook = _thread_excepthook


def _hide_console():
    if sys.platform == "win32":
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass


_hide_console()


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LAN File Server - Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:16px}
.card{background:#fff;border-radius:16px;padding:40px 30px;width:100%;max-width:380px;box-shadow:0 20px 60px rgba(0,0,0,.25);text-align:center}
.logo{font-size:44px;margin-bottom:6px}
.card h1{font-size:22px;color:#333;margin-bottom:6px}
.sub{color:#999;font-size:13px;margin-bottom:22px}
.card input{width:100%;padding:12px 14px;margin-bottom:14px;border:1px solid #ddd;border-radius:10px;font-size:15px;outline:none}
.card input:focus{border-color:#667eea;box-shadow:0 0 0 3px rgba(102,126,234,.15)}
.card button{width:100%;padding:12px;border:0;border-radius:10px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:16px;cursor:pointer}
.card button:hover{opacity:.9}
.error{background:#fdecea;color:#c0392b;border:1px solid #f5c6cb;border-radius:8px;padding:10px;font-size:14px;margin-bottom:14px}
</style>
</head>
<body>
<div class="card">
<div class="logo">&#128193;</div>
<h1>LAN File Server</h1>
<p class="sub">Please enter your username and password</p>
__ERROR__
<form method="post" action="/login">
<input type="text" name="username" placeholder="Username" required autofocus>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Log In</button>
</form>
</div>
</body>
</html>
"""

LIST_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LAN File Server</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;background:#f4f6fa;min-height:100vh}
header{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:16px}
header h1{font-size:19px}
.breadcrumbs{margin-top:10px;font-size:13px;display:flex;flex-wrap:wrap;align-items:center}
.breadcrumbs a{color:#e8eafd;text-decoration:none}
.breadcrumbs a:hover{text-decoration:underline}
.breadcrumbs .sep{opacity:.6;margin:0 2px}
.toolbar{max-width:900px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;padding:14px 16px;gap:10px}
.toolbar .cur{color:#666;font-size:13px;word-break:break-all}
.toolbar .logout{color:#667eea;text-decoration:none;font-size:13px;white-space:nowrap}
.container{max-width:900px;margin:0 auto;padding:0 12px 30px}
.list{background:#fff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.05);overflow:hidden}
.item{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid #f0f0f0}
.item:last-child{border-bottom:0}
.icon{font-size:22px;width:28px;text-align:center;flex-shrink:0}
.name{flex:1;min-width:0}
.name a{color:#333;text-decoration:none;word-break:break-all}
.name a:hover{color:#667eea}
.size{color:#999;font-size:13px;white-space:nowrap}
.dl{background:#667eea;color:#fff;text-decoration:none;padding:6px 14px;border-radius:16px;font-size:13px;white-space:nowrap}
.dl:hover{background:#5568d3}
.empty{text-align:center;color:#999;padding:48px 16px;font-size:14px}
@media (max-width:600px){
.item{flex-wrap:wrap}
.size{order:3;width:100%;padding-left:38px}
header h1{font-size:17px}
}
</style>
</head>
<body>
<header>
<h1>&#128193; LAN File Server</h1>
<div class="breadcrumbs">__BREADCRUMBS__</div>
</header>
<div class="toolbar">
<span class="cur">Current path: __CUR__</span>
__LOGOUT__
</div>
<div class="container">
<div class="list">__ITEMS__</div>
</div>
</body>
</html>
"""

NOT_FOUND_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>404 - LAN File Server</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,"Segoe UI",Roboto,sans-serif;background:#f4f6fa;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{text-align:center;background:#fff;border-radius:16px;padding:48px;box-shadow:0 2px 10px rgba(0,0,0,.05)}
.box h1{font-size:52px;color:#667eea}
.box p{color:#666;margin:12px 0 20px}
.box a{color:#667eea;text-decoration:none;font-size:14px}
</style>
</head>
<body>
<div class="box">
<h1>404</h1>
<p>Page Not Found</p>
<a href="/">Back to Home</a>
</div>
</body>
</html>
"""


def format_size(n):
    if n < 1024:
        return "{} B".format(n)
    for unit in ("KB", "MB", "GB", "TB"):
        n /= 1024.0
        if n < 1024 or unit == "TB":
            return "{:.1f} {}".format(n, unit)


def build_breadcrumbs(rel):
    parts = [p for p in rel.split("/") if p]
    out = ['<a href="/">&#127968; Home</a>']
    acc = []
    for p in parts:
        acc.append(p)
        link = "/?p=" + urllib.parse.quote("/".join(acc), safe="/")
        out.append('<span class="sep">/</span>')
        out.append('<a href="{}">{}</a>'.format(link, html.escape(p)))
    return "".join(out)


def build_items(base, rel):
    try:
        entries = []
        for name in os.listdir(base):
            full = os.path.join(base, name)
            is_dir = os.path.isdir(full)
            if is_dir:
                entries.append((name, True, ""))
            else:
                entries.append((name, False, format_size(os.path.getsize(full))))
    except OSError:
        return '<div class="empty">Failed to read directory</div>'
    entries.sort(key=lambda e: (not e[1], e[0].lower()))
    if not entries:
        return '<div class="empty">&#128228; Empty folder</div>'
    rows = []
    for name, is_dir, size in entries:
        child = (rel + "/" + name) if rel else name
        enc = urllib.parse.quote(child, safe="/")
        if is_dir:
            rows.append(
                '<div class="item"><span class="icon">&#128193;</span>'
                '<span class="name"><a href="/?p={0}">{1}</a></span>'
                '<span class="size">Folder</span></div>'.format(enc, html.escape(name)))
        else:
            rows.append(
                '<div class="item"><span class="icon">&#128196;</span>'
                '<span class="name"><a href="/files/{0}">{1}</a></span>'
                '<span class="size">{2}</span>'
                '<a class="dl" href="/files/{0}">Download</a></div>'.format(enc, html.escape(name), size))
    return "".join(rows)


class FileHandler(BaseHTTPRequestHandler):
    server_version = "LanFileServer/1.1.0"
    root_dir = ""
    require_auth = False
    username = ""
    password = ""
    sessions = {}

    def log_message(self, format, *args):
        pass

    def _send_html(self, status, body):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _redirect(self, location, set_cookie=None):
        self.send_response(302)
        self.send_header("Location", location)
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _has_session(self):
        if not self.require_auth:
            return True
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("session="):
                return part[len("session="):] in self.sessions
        return False

    def _safe_path(self, rel):
        root = os.path.realpath(self.root_dir)
        target = os.path.realpath(os.path.join(root, rel))
        if target != root and not target.startswith(root + os.sep):
            return None
        return target

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == "/logout":
            cookie = self.headers.get("Cookie", "")
            for part in cookie.split(";"):
                part = part.strip()
                if part.startswith("session="):
                    self.sessions.pop(part[len("session="):], None)
            self._redirect("/", set_cookie="session=; HttpOnly; Path=/; Max-Age=0")
            return

        if not self._has_session():
            if path == "/":
                err = "1" in urllib.parse.parse_qs(parsed.query).get("err", [])
                self._send_html(200, LOGIN_PAGE.replace(
                    "__ERROR__",
                    '<div class="error">Invalid username or password</div>' if err else ""))
            else:
                self._redirect("/")
            return

        if path == "/":
            rel = urllib.parse.parse_qs(parsed.query).get("p", [""])[0].strip("/")
            target = self._safe_path(rel)
            if target is None or not os.path.isdir(target):
                self._send_html(404, NOT_FOUND_PAGE)
                return
            page = LIST_PAGE
            page = page.replace("__BREADCRUMBS__", build_breadcrumbs(rel))
            page = page.replace("__ITEMS__", build_items(target, rel))
            page = page.replace("__CUR__", html.escape(rel if rel else "/"))
            page = page.replace("__LOGOUT__",
                                '<a class="logout" href="/logout">Log Out</a>' if self.require_auth else "")
            self._send_html(200, page)
            return

        if path.startswith("/files/"):
            rel = path[len("/files/"):].strip("/")
            if not rel:
                self._send_html(404, NOT_FOUND_PAGE)
                return
            target = self._safe_path(rel)
            if target is None or not os.path.isfile(target):
                self._send_html(404, NOT_FOUND_PAGE)
                return
            self._stream_file(target)
            return

        self._send_html(404, NOT_FOUND_PAGE)

    def _stream_file(self, target):
        try:
            size = os.path.getsize(target)
        except OSError:
            self._send_html(404, NOT_FOUND_PAGE)
            return
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        fname = os.path.basename(target)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition",
                         "attachment; filename*=UTF-8''{}".format(urllib.parse.quote(fname)))
        self.end_headers()
        try:
            with open(target, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def do_POST(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path != "/login":
            self._send_html(404, NOT_FOUND_PAGE)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        body = self.rfile.read(length).decode("utf-8", "replace")
        form = urllib.parse.parse_qs(body)
        username = form.get("username", [""])[0]
        password = form.get("password", [""])[0]
        if (hmac.compare_digest(username.encode("utf-8"), self.username.encode("utf-8"))
                and hmac.compare_digest(password.encode("utf-8"), self.password.encode("utf-8"))):
            token = secrets.token_hex(32)
            self.sessions[token] = username
            self._redirect("/", set_cookie="session={}; HttpOnly; Path=/".format(token))
        else:
            self._redirect("/?err=1")


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    sg.theme("SystemDefault")

    layout = [
        [
            sg.Text("Shared Folder:"),
            sg.Input(key="-FOLDER-", enable_events=True),
            sg.FolderBrowse("Browse"),
        ],
        [
            sg.Text("Port:"),
            sg.Input("8080", key="-PORT-", size=(10, 1)),
            sg.Button("Start Sharing", key="-START-", button_color=("white", "green")),
            sg.Button("Stop Sharing", key="-STOP-", button_color=("white", "red"), disabled=True),
            sg.Button("Copy Link", key="-COPY-"),
            sg.Button("About", key="-ABOUT-"),
        ],
        [
            sg.Text("Username:"),
            sg.Input(key="-USER-", size=(12, 1)),
            sg.Text("Password:"),
            sg.Input(key="-PASS-", size=(12, 1), password_char="*"),
            sg.Checkbox("Enable Password Protection", key="-ENABLE-PASS-", default=False),
        ],
        [sg.Text("Log:", font=("Microsoft YaHei", 10, "bold"))],
        [sg.Multiline("", key="-LOG-", size=(70, 12), disabled=True, autoscroll=True)],
    ]

    window = sg.Window("LAN File Server V1.1.0", layout, finalize=True)

    server_thread = None
    http_server = None

    def log(msg):
        window["-LOG-"].print(msg)

    log("Tip: When Windows Firewall pops up, please check [Private / LAN Network], otherwise other devices cannot access")

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            if http_server is not None:
                try:
                    http_server.shutdown()
                    http_server.server_close()
                except Exception:
                    pass
            break

        elif event == "-START-":
            folder = values["-FOLDER-"].strip()
            port_str = values["-PORT-"].strip()

            if not folder or not os.path.isdir(folder):
                log("Error: Please select an existing folder")
                continue

            try:
                port = int(port_str)
                if port < 1 or port > 65535:
                    raise ValueError
            except ValueError:
                log("Error: Port must be a number between 1-65535")
                continue

            use_pass = values["-ENABLE-PASS-"]
            username = values["-USER-"].strip()
            password = values["-PASS-"]
            if use_pass and (not username or not password):
                log("Error: Username and password cannot be empty when password protection is enabled")
                continue

            local_ip = get_local_ip()

            FileHandler.root_dir = folder
            FileHandler.require_auth = use_pass
            FileHandler.username = username
            FileHandler.password = password
            FileHandler.sessions = {}

            try:
                http_server = ThreadingHTTPServer(("0.0.0.0", port), FileHandler)
                http_server.block_on_close = False
            except OSError as e:
                log("Error: Cannot bind port {} - {}".format(port, e))
                continue

            server_thread = threading.Thread(
                target=http_server.serve_forever, daemon=True
            )
            server_thread.start()

            log("Sharing started!")
            if use_pass:
                log("Password protection enabled")
            log("Local access: http://127.0.0.1:{}".format(port))
            log("LAN access: http://{}:{}".format(local_ip, port))

            window["-START-"].update(disabled=True)
            window["-STOP-"].update(disabled=False)

        elif event == "-STOP-":
            if http_server is not None:
                try:
                    http_server.shutdown()
                    http_server.server_close()
                except Exception:
                    pass
                http_server = None
                server_thread = None
                log("Sharing stopped")
            window["-START-"].update(disabled=False)
            window["-STOP-"].update(disabled=True)

        elif event == "-COPY-":
            port_str = values["-PORT-"].strip()
            local_ip = get_local_ip()
            try:
                port = int(port_str)
            except ValueError:
                port = 8080
            link = "http://{}:{}".format(local_ip, port)
            try:
                sg.clipboard_set(link)
                log("Link copied: {}".format(link))
            except Exception:
                log("Copy failed, please copy manually: {}".format(link))

        elif event == "-ABOUT-":
            sg.popup(
                "LAN File Server V1.1.0\n"
                "A simple LAN file sharing tool\n"
                "Feedback email: 77070689@qq.com\n"
                "For LAN use only. Do not expose to the public internet",
                title="About",
            )

    window.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _log_crash(*sys.exc_info(), title="Main Program Crash")
