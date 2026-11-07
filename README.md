# 局域网文件库 (LAN File Server)

一个基于 Python + PySimpleGUI 的局域网文件共享小工具：把本地文件夹一键共享给同一局域网内的其他设备，对方用浏览器打开链接即可浏览、下载文件。

## 功能特性

- 选择任意文件夹，一键共享（底层使用 Python 内置 http.server）
- 自动获取本机局域网 IP，显示本机与局域网访问地址
- 网页端自带现代化登录页与文件浏览页，手机、电脑浏览器均适配（不再使用 http.server 原生目录列表）
- 可选密码保护：勾选"启用密码保护"并设置用户名密码，访问需先登录
- 一键复制分享链接，方便发给微信 / QQ
- 启动、停止共享不卡界面（服务运行在后台线程）
- 大文件流式传输，不占内存
- 程序崩溃时自动在程序目录生成 `error_log.txt`，方便排查问题
- 提供中文版和英文版

## 快速使用

### 方式一：直接运行 exe（推荐，无需安装 Python）

从本仓库的 **Releases** 页面下载对应版本的 exe，双击运行：

1. 点"浏览 / Browse"选择要共享的文件夹
2. 端口默认 8080，可自行修改
3. 想加密码就填写用户名、密码，并勾选"启用密码保护"（不勾选则局域网内无需登录直接访问）
4. 点"启动共享 / Start Sharing"，把日志框里显示的局域网地址发给对方；对方用浏览器打开，输入账号密码（如已启用）即可浏览下载

### 方式二：从源码运行

```bash
pip install PySimpleGUI==4.60.5.1
python Untitled-1.py          # 中文版
python lan_file_server_en.py  # 英文版
```

## 打包成 exe

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "LAN_File_Server_CN_v1.1.0" --hidden-import=http.server Untitled-1.py
pyinstaller --onefile --windowed --name "LAN_File_Server_EN_v1.1.0" --hidden-import=http.server lan_file_server_en.py
```

## 注意事项

- 本程序仅供局域网内使用，请勿暴露到公网
- 密码保护为可选项：不勾选时局域网内任何人都能访问，建议共享敏感文件时启用
- 网页使用 HTTP 明文传输，同一网络下抓包可见账号密码，请勿在公共 WiFi 环境共享敏感文件
- 第一次启动时 Windows 防火墙会弹窗，请勾选"专用网络 / 局域网"，否则其他设备无法访问

## 反馈

Bug 反馈邮箱：77070689@qq.com

## 版本

V1.1.0
