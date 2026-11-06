import os
import sys
import socket
import threading
import traceback
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

import PySimpleGUI as sg


def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _base_dir()
ERROR_LOG = os.path.join(BASE_DIR, "error_log.txt")


def _log_crash(exc_type, exc_value, exc_tb, title="未捕获异常"):
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
    _log_crash(exc_type, exc_value, exc_tb, "主线程未捕获异常")


def _thread_excepthook(args):
    _log_crash(args.exc_type, args.exc_value, args.exc_traceback, "子线程异常")


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


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, directory, *args, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, format, *args):
        pass


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
            sg.Text("共享文件夹:"),
            sg.Input(key="-FOLDER-", enable_events=True),
            sg.FolderBrowse("浏览"),
        ],
        [
            sg.Text("端口:"),
            sg.Input("8080", key="-PORT-", size=(10, 1)),
            sg.Button("启动共享", key="-START-", button_color=("white", "green")),
            sg.Button("停止共享", key="-STOP-", button_color=("white", "red"), disabled=True),
            sg.Button("复制分享链接", key="-COPY-"),
            sg.Button("关于", key="-ABOUT-"),
        ],
        [sg.Text("日志:", font=("Microsoft YaHei", 10, "bold"))],
        [sg.Multiline("", key="-LOG-", size=(70, 12), disabled=True, autoscroll=True)],
    ]

    window = sg.Window("局域网文件库 V1.0.0", layout, finalize=True)

    server_thread = None
    http_server = None

    def log(msg):
        window["-LOG-"].print(msg)

    log("提示: Windows 弹防火墙时请勾选【专用 / 局域网网络】，否则其他设备无法访问")

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
                log("错误: 请选择一个存在的文件夹")
                continue

            try:
                port = int(port_str)
                if port < 1 or port > 65535:
                    raise ValueError
            except ValueError:
                log("错误: 端口必须是 1-65535 的数字")
                continue

            local_ip = get_local_ip()

            try:
                handler = partial(QuietHandler, folder)
                http_server = HTTPServer(("0.0.0.0", port), handler)
            except OSError as e:
                log("错误: 无法绑定端口 {} - {}".format(port, e))
                continue

            server_thread = threading.Thread(
                target=http_server.serve_forever, daemon=True
            )
            server_thread.start()

            log("共享已启动!")
            log("本机访问: http://127.0.0.1:{}".format(port))
            log("局域网访问: http://{}:{}".format(local_ip, port))

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
                log("共享已停止")
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
                log("已复制链接: {}".format(link))
            except Exception:
                log("复制失败，请手动复制: {}".format(link))

        elif event == "-ABOUT-":
            sg.popup(
                "局域网文件库 V1.0.0\n"
                "局域网内文件共享小工具\n"
                "反馈 Bug 邮箱：77070689@qq.com\n"
                "温馨提示：本程序仅限局域网内使用，请勿暴露到公网",
                title="关于",
            )

    window.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _log_crash(*sys.exc_info(), title="主程序崩溃")
