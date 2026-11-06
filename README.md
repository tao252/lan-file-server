# 局域网文件库 (LAN File Server)

一个基于 Python + PySimpleGUI 的局域网文件共享小工具：把本地文件夹一键共享给同一局域网内的其他设备，对方用浏览器打开链接即可浏览、下载文件。

## 功能特性

- 选择任意文件夹，一键共享（底层使用 Python 内置 http.server）
- 自动获取本机局域网 IP，显示本机与局域网访问地址
- 一键复制分享链接，方便发给微信 / QQ
- 启动、停止共享不卡界面（服务运行在后台线程）
- 程序崩溃时自动在程序目录生成 `error_log.txt`，方便排查问题
- 提供中文版和英文版

## 快速使用

### 方式一：直接运行 exe（推荐，无需安装 Python）

从本仓库的 **Releases** 页面下载对应版本的 exe，双击运行：

1. 点"浏览 / Browse"选择要共享的文件夹
2. 端口默认 8080，可自行修改
3. 点"启动共享 / Start Sharing"，把日志框里显示的局域网地址发给对方即可访问

### 方式二：从源码运行

```bash
pip install PySimpleGUI==4.60.5.1
python Untitled-1.py          # 中文版
python lan_file_server_en.py  # 英文版
```

## 打包成 exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "局域网文件库_v1.0.0" --hidden-import=http.server Untitled-1.py
pyinstaller --onefile --windowed --name "LAN_File_Server_EN_v1.0.0" --hidden-import=http.server lan_file_server_en.py
```

## 注意事项

- 本程序仅供局域网内使用，请勿暴露到公网（没有密码鉴权，局域网内任何人都能访问共享内容）
- 第一次启动时 Windows 防火墙会弹窗，请勾选"专用网络 / 局域网"，否则其他设备无法访问

## 反馈

Bug 反馈邮箱：77070689@qq.com

## 版本

V1.0.0
