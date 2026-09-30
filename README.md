# WeCom Watchdog Console

桌面 / 浏览器控制台：对接本地 `wecom-group-watchdog`（默认 http://127.0.0.1:8092）。

## 功能

1. **定时校验间隔**：5 / 10 / 15 / 30 分钟或自定义，调用 `POST /admin/scan-interval?minutes=` 热更新服务端 APScheduler。
2. **立即扫描**：`POST /admin/scan?force=true`
3. **模拟话术问答**：`POST /admin/suggest`，自定义客户问题，返回三段建议（问题类型 / 问题内容 / 回复建议）。

## 依赖

- Python 3.10+
- watchdog 服务已启动（含 `/admin/suggest`、`/admin/scan-interval`）

## 启动

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt
run.bat
```

`run.bat` 默认打开 **科技感浏览器 HUD**（http://127.0.0.1:8765）：深空背景、网格漂移、玻璃拟态卡片、青霓虹描边（参考开源 cyber dashboard / glassmorphism 风格）。

```bash
run.bat
# 或
.venv\Scripts\python app\web_ui.py
```

若仍要桌面 Tk 窗口：

```bash
set USE_DESKTOP=1
run.bat
```

## 仓库

https://github.com/Wanpl-Java/wecom-watchdog-gui
