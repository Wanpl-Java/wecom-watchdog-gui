# WeCom Watchdog Console

原生 **桌面 GUI 窗口**（CustomTkinter 深色科技风），对接本地 `wecom-group-watchdog`（默认 http://127.0.0.1:8092）。

## 功能

1. **定时校验间隔**：5 / 10 / 15 / 30 分钟或自定义  
2. **立即扫描**  
3. **模拟话术问答**  

## 启动（桌面窗口）

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
run.bat
```

`run.bat` **默认打开桌面 GUI**。会自动设置 `TCL_LIBRARY` / `TK_LIBRARY`（修复 Python 3.13 找不到 Tcl 的问题）。  
仅当桌面启动失败时，才回退浏览器版。

```bash
# 仅桌面
.venv\Scripts\python app\main.py

# 仅浏览器（可选）
.venv\Scripts\python app\web_ui.py
```

## 仓库

https://github.com/Wanpl-Java/wecom-watchdog-gui
