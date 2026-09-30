"""Browser-based console — no Tk/Tcl required."""
from __future__ import annotations

import threading
import webbrowser
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from client import WatchdogClient

app = FastAPI(title="WeCom Watchdog Console")
DEFAULT_BASE = "http://127.0.0.1:8092"


class IntervalBody(BaseModel):
    base_url: str = DEFAULT_BASE
    minutes: int = Field(5, ge=0, le=1440)


class SuggestBody(BaseModel):
    base_url: str = DEFAULT_BASE
    question: str
    group_name: str = "【JS】GUI模拟群"


class ScanBody(BaseModel):
    base_url: str = DEFAULT_BASE


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>WeCom Watchdog Console</title>
  <style>
    :root { --bg:#f4f7fb; --card:#fff; --ink:#1a2332; --muted:#5b6b7c; --acc:#2563eb; --line:#d8e0ea; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
           background: linear-gradient(160deg,#eef3ff,#f7fafc 45%,#edf6f3); color:var(--ink); }
    main { max-width: 920px; margin: 32px auto; padding: 0 16px 48px; }
    h1 { font-size: 1.6rem; margin: 0 0 6px; letter-spacing: .02em; }
    .sub { color: var(--muted); margin-bottom: 20px; }
    .card { background: var(--card); border: 1px solid var(--line); border-radius: 14px;
            padding: 18px 18px 14px; margin-bottom: 16px; box-shadow: 0 8px 24px rgba(26,35,50,.05); }
    label { display:block; font-size:.85rem; color:var(--muted); margin: 8px 0 4px; }
    input, select, textarea { width:100%; padding:10px 12px; border:1px solid var(--line);
      border-radius:10px; font: inherit; background:#fbfdff; }
    textarea { min-height: 110px; resize: vertical; }
    .row { display:flex; gap:10px; flex-wrap:wrap; align-items:end; }
    .row > div { flex:1; min-width:140px; }
    button { border:0; border-radius:10px; padding:10px 14px; font:inherit; cursor:pointer;
             background:var(--acc); color:#fff; }
    button.secondary { background:#e8eef8; color:var(--ink); }
    button:disabled { opacity:.6; cursor:wait; }
    #status { font-size:.92rem; color:var(--muted); margin-top:8px; white-space:pre-wrap; }
    #out { white-space:pre-wrap; font-family: ui-monospace, Consolas, monospace; font-size:.9rem;
           background:#0f172a; color:#e2e8f0; padding:14px; border-radius:12px; min-height:220px; }
  </style>
</head>
<body>
<main>
  <h1>WeCom Watchdog Console</h1>
  <p class="sub">定时校验 + 模拟话术问答（浏览器版，不依赖 Tcl/Tk）</p>

  <section class="card">
    <label>Watchdog 地址</label>
    <div class="row">
      <div><input id="base" value="http://127.0.0.1:8092"/></div>
      <button class="secondary" onclick="health()">检测连接</button>
    </div>
    <div id="status">状态：未检测</div>
  </section>

  <section class="card">
    <label>定时校验间隔</label>
    <div class="row">
      <div>
        <select id="preset" onchange="syncCustom()">
          <option value="5">5 分钟</option>
          <option value="10">10 分钟</option>
          <option value="15">15 分钟</option>
          <option value="30">30 分钟</option>
          <option value="custom">自定义</option>
        </select>
      </div>
      <div>
        <label>自定义(分钟)</label>
        <input id="customMin" type="number" min="0" max="1440" value="5"/>
      </div>
      <button onclick="setIntervalMin()">应用到 Watchdog</button>
      <button class="secondary" onclick="scan()">立即扫描</button>
    </div>
  </section>

  <section class="card">
    <label>样例问题</label>
    <select id="sample" onchange="document.getElementById('q').value=this.value">
      <option>JumpServer远程应用发布机怎么部署</option>
      <option>登录提示配置文件有问题无法登录 DOMAINS</option>
      <option>Tinker 离线怎么办</option>
      <option>资产连接超时怎么排查</option>
    </select>
    <label>模拟群名</label>
    <input id="group" value="【JS】GUI模拟群"/>
    <label>自定义问题</label>
    <textarea id="q">JumpServer远程应用发布机怎么部署</textarea>
    <div class="row" style="margin-top:10px">
      <button onclick="suggest()">发送模拟问答</button>
      <button class="secondary" onclick="document.getElementById('out').textContent=''">清空输出</button>
    </div>
  </section>

  <section class="card">
    <label>输出</label>
    <pre id="out"></pre>
  </section>
</main>
<script>
function base(){ return document.getElementById('base').value.trim() || 'http://127.0.0.1:8092'; }
function minutes(){
  const p = document.getElementById('preset').value;
  if(p !== 'custom') return parseInt(p,10);
  return parseInt(document.getElementById('customMin').value||'5',10);
}
function syncCustom(){
  if(document.getElementById('preset').value !== 'custom'){
    document.getElementById('customMin').value = document.getElementById('preset').value;
  }
}
async function health(){
  const r = await fetch('/api/health', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({base_url: base()})});
  const d = await r.json();
  document.getElementById('status').textContent = d.ok
    ? `状态：在线 | mode=${d.workbuddy_mode} | scan=${d.scan_interval_minutes}min | source=${d.message_source}`
    : `状态：离线 — ${d.error||r.status}`;
}
async function setIntervalMin(){
  const r = await fetch('/api/interval', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({base_url: base(), minutes: minutes()})});
  const d = await r.json();
  document.getElementById('status').textContent = d.ok
    ? `已设置服务端定时校验: ${d.scan_interval_minutes} 分钟`
    : `设置失败: ${d.error||r.status}`;
  if(d.ok) health();
}
async function scan(){
  document.getElementById('status').textContent = '正在 force scan…';
  const r = await fetch('/api/scan', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({base_url: base()})});
  const d = await r.json();
  document.getElementById('out').textContent = JSON.stringify(d, null, 2);
  document.getElementById('status').textContent = d.error ? `scan 失败: ${d.error}` : 'scan 完成';
}
async function suggest(){
  const q = document.getElementById('q').value.trim();
  if(!q){ alert('请先填写模拟问题'); return; }
  document.getElementById('status').textContent = '正在生成建议（可能需 10–60 秒）…';
  const r = await fetch('/api/suggest', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({base_url: base(), question:q, group_name: document.getElementById('group').value})});
  const d = await r.json();
  if(d.error){
    document.getElementById('status').textContent = `suggest 失败: ${d.error}`;
    document.getElementById('out').textContent = d.error;
    return;
  }
  document.getElementById('out').textContent =
`=== 模拟问答 ===
群: ${d.group_name}
问: ${d.question}
来源: ${d.source}

${d.suggestion}`;
  document.getElementById('status').textContent = `suggest ok source=${d.source}`;
}
syncCustom();
health();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.post("/api/health")
def api_health(body: ScanBody) -> Dict[str, Any]:
    try:
        return WatchdogClient(body.base_url).healthz()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


@app.post("/api/interval")
def api_interval(body: IntervalBody) -> Dict[str, Any]:
    try:
        return WatchdogClient(body.base_url).set_interval(body.minutes)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


@app.post("/api/scan")
def api_scan(body: ScanBody) -> Dict[str, Any]:
    try:
        return WatchdogClient(body.base_url).force_scan()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


@app.post("/api/suggest")
def api_suggest(body: SuggestBody) -> Dict[str, Any]:
    if not body.question.strip():
        raise HTTPException(400, "question required")
    try:
        return WatchdogClient(body.base_url).suggest(body.question, group_name=body.group_name)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def main() -> None:
    def _open() -> None:
        webbrowser.open("http://127.0.0.1:8765/")

    threading.Timer(1.0, _open).start()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
