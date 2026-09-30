"""WeCom Watchdog Console — native desktop GUI (cyber dark)."""
from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Optional

# Fix common Windows Python embed where Tcl path resolves to .../lib/tcl8.6
def _fix_tcl_env() -> None:
    candidates = [
        Path(r"D:\Python313"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python313",
        Path(sys.base_prefix),
        Path(sys.prefix),
    ]
    for root in candidates:
        tcl = root / "tcl" / "tcl8.6"
        tk_ = root / "tcl" / "tk8.6"
        if (tcl / "init.tcl").is_file():
            os.environ["TCL_LIBRARY"] = str(tcl)
            if (tk_ / "tk.tcl").is_file():
                os.environ["TK_LIBRARY"] = str(tk_)
            break


_fix_tcl_env()

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

import customtkinter as ctk

from client import WatchdogClient

PRESETS = [("5 分钟", 5), ("10 分钟", 10), ("15 分钟", 15), ("30 分钟", 30), ("自定义", -1)]
SAMPLES = [
    "JumpServer远程应用发布机怎么部署",
    "登录提示配置文件有问题无法登录 DOMAINS",
    "Tinker 离线怎么办",
    "资产连接超时怎么排查",
]

# Cyber HUD palette
BG = "#05060f"
PANEL = "#0c1224"
PANEL2 = "#101830"
CYAN = "#22d3ee"
MINT = "#34d399"
TEXT = "#e8eefc"
MUTED = "#8b9bb8"
LINE = "#1a3a4a"


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("WATCHDOG CONSOLE // JumpServer")
        self.geometry("1040x780")
        self.minsize(900, 680)
        self.configure(fg_color=BG)

        self.client = WatchdogClient()
        self._auto_job: Optional[str] = None

        self._build()
        self.after(400, self.refresh_status)

    def _card(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        wrap = ctk.CTkFrame(
            parent,
            fg_color=PANEL,
            corner_radius=16,
            border_width=1,
            border_color=LINE,
        )
        head = ctk.CTkLabel(
            wrap,
            text=title,
            text_color=CYAN,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            anchor="w",
        )
        head.pack(fill="x", padx=16, pady=(14, 6))
        body = ctk.CTkFrame(wrap, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        return body

    def _build(self) -> None:
        # Hero
        hero = ctk.CTkFrame(self, fg_color="transparent")
        hero.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(
            hero,
            text="FIT2CLOUD  ·  JUMPSERVER OPS",
            text_color=CYAN,
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).pack(fill="x")
        row = ctk.CTkFrame(hero, fg_color="transparent")
        row.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(
            row,
            text="WATCHDOG CONSOLE",
            text_color=TEXT,
            font=ctk.CTkFont(size=26, weight="bold"),
            anchor="w",
        ).pack(side="left")
        self.live_lbl = ctk.CTkLabel(
            row,
            text="● STANDBY",
            text_color="#fbbf24",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.live_lbl.pack(side="right", padx=(8, 0))

        ctk.CTkLabel(
            hero,
            text="原生桌面窗口 · 定时校验 · 模拟话术问答",
            text_color=MUTED,
            font=ctk.CTkFont(size=13),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Link + interval
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=8)
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)

        link_body = self._card(top, "01  //  LINK")
        link_body.master.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ctk.CTkLabel(link_body, text="Watchdog 地址", text_color=MUTED, anchor="w").pack(fill="x")
        self.base_var = tk.StringVar(value="http://127.0.0.1:8092")
        ctk.CTkEntry(
            link_body,
            textvariable=self.base_var,
            fg_color=PANEL2,
            border_color=LINE,
            text_color=TEXT,
            height=36,
        ).pack(fill="x", pady=(4, 8))
        ctk.CTkButton(
            link_body,
            text="检测连接  PING",
            command=self.refresh_status,
            fg_color="#0e7490",
            hover_color="#0891b2",
            text_color=TEXT,
            height=36,
        ).pack(fill="x")
        self.status_var = tk.StringVar(value="状态：未检测")
        ctk.CTkLabel(
            link_body,
            textvariable=self.status_var,
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
            anchor="w",
            wraplength=420,
            justify="left",
        ).pack(fill="x", pady=(10, 0))

        int_body = self._card(top, "02  //  INTERVAL")
        int_body.master.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ctk.CTkLabel(int_body, text="定时校验间隔", text_color=MUTED, anchor="w").pack(fill="x")
        self.interval_choice = tk.StringVar(value="5 分钟")
        ctk.CTkOptionMenu(
            int_body,
            variable=self.interval_choice,
            values=[p[0] for p in PRESETS],
            fg_color=PANEL2,
            button_color="#0e7490",
            button_hover_color="#0891b2",
            dropdown_fg_color=PANEL,
            text_color=TEXT,
            height=36,
        ).pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(int_body, text="自定义（分钟）", text_color=MUTED, anchor="w").pack(fill="x")
        self.custom_min = tk.StringVar(value="5")
        ctk.CTkEntry(
            int_body,
            textvariable=self.custom_min,
            fg_color=PANEL2,
            border_color=LINE,
            text_color=TEXT,
            height=36,
        ).pack(fill="x", pady=(4, 8))
        btn_row = ctk.CTkFrame(int_body, fg_color="transparent")
        btn_row.pack(fill="x")
        ctk.CTkButton(
            btn_row,
            text="应用到服务端",
            command=self.apply_interval,
            fg_color=CYAN,
            hover_color="#67e8f9",
            text_color="#041018",
            height=36,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            btn_row,
            text="立即扫描",
            command=self.do_scan,
            fg_color=PANEL2,
            hover_color="#16324a",
            border_width=1,
            border_color=CYAN,
            text_color=CYAN,
            height=36,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.gui_auto = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            int_body,
            text="GUI 计时提醒（到点询问是否扫描）",
            variable=self.gui_auto,
            command=self.toggle_gui_timer,
            text_color=MUTED,
            fg_color=CYAN,
            hover_color="#67e8f9",
            border_color=LINE,
        ).pack(anchor="w", pady=(10, 0))

        # Simulate
        mid_wrap = ctk.CTkFrame(self, fg_color="transparent")
        mid_wrap.pack(fill="both", expand=True, padx=18, pady=8)
        sim = self._card(mid_wrap, "03  //  SIMULATE Q&A")
        sim.master.pack(fill="both", expand=True)

        ctk.CTkLabel(sim, text="样例问题", text_color=MUTED, anchor="w").pack(fill="x")
        self.q_var = tk.StringVar(value=SAMPLES[0])
        ctk.CTkOptionMenu(
            sim,
            variable=self.q_var,
            values=SAMPLES,
            command=self._on_sample,
            fg_color=PANEL2,
            button_color="#0e7490",
            button_hover_color="#0891b2",
            dropdown_fg_color=PANEL,
            text_color=TEXT,
            height=36,
        ).pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(sim, text="模拟群名", text_color=MUTED, anchor="w").pack(fill="x")
        self.group_var = tk.StringVar(value="【JS】GUI模拟群")
        ctk.CTkEntry(
            sim,
            textvariable=self.group_var,
            fg_color=PANEL2,
            border_color=LINE,
            text_color=TEXT,
            height=36,
        ).pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(sim, text="自定义问题", text_color=MUTED, anchor="w").pack(fill="x")
        self.q_text = ctk.CTkTextbox(
            sim,
            height=90,
            fg_color=PANEL2,
            border_color=LINE,
            border_width=1,
            text_color=TEXT,
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.q_text.pack(fill="x", pady=(4, 8))
        self.q_text.insert("1.0", SAMPLES[0])

        act = ctk.CTkFrame(sim, fg_color="transparent")
        act.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            act,
            text="发送模拟问答",
            command=self.do_suggest,
            fg_color=CYAN,
            hover_color="#67e8f9",
            text_color="#041018",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            act,
            text="清空输出",
            command=self.clear_out,
            fg_color=PANEL2,
            hover_color="#16324a",
            border_width=1,
            border_color=LINE,
            text_color=MUTED,
            height=40,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        ctk.CTkLabel(sim, text="04  //  OUTPUT", text_color=CYAN, anchor="w").pack(fill="x", pady=(4, 4))
        self.out = ctk.CTkTextbox(
            sim,
            height=220,
            fg_color="#06141e",
            border_color="#1a4a3a",
            border_width=1,
            text_color="#d1fae5",
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.out.pack(fill="both", expand=True)
        self.out.insert("1.0", "等待指令…\n")

        self.log_var = tk.StringVar(value="")
        ctk.CTkLabel(
            self,
            textvariable=self.log_var,
            text_color=MUTED,
            font=ctk.CTkFont(size=12),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(0, 12))

    def _on_sample(self, value: str) -> None:
        self.q_text.delete("1.0", "end")
        self.q_text.insert("1.0", value)

    def _minutes(self) -> int:
        choice = self.interval_choice.get()
        for label, m in PRESETS:
            if choice == label and m > 0:
                return m
        try:
            return max(0, int(self.custom_min.get().strip()))
        except ValueError:
            return 5

    def _sync_client(self) -> None:
        self.client = WatchdogClient(self.base_var.get().strip() or "http://127.0.0.1:8092")

    def _append(self, text: str) -> None:
        self.out.insert("end", text + "\n")
        self.out.see("end")

    def _set_log(self, msg: str) -> None:
        self.log_var.set(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def _set_live(self, online: bool, text: str) -> None:
        self.live_lbl.configure(text=f"● {text}", text_color=MINT if online else "#fb7185")

    def refresh_status(self) -> None:
        self._sync_client()

        def work() -> None:
            try:
                data = self.client.healthz()
                msg = (
                    f"ONLINE · mode={data.get('workbuddy_mode')} · "
                    f"scan={data.get('scan_interval_minutes')}min · "
                    f"source={data.get('message_source')}"
                )
                self.after(0, lambda: self.status_var.set(msg))
                self.after(0, lambda: self._set_live(True, "ONLINE"))
                self.after(0, lambda: self._set_log("healthz ok"))
            except Exception as e:  # noqa: BLE001
                self.after(0, lambda: self.status_var.set(f"OFFLINE — {e}"))
                self.after(0, lambda: self._set_live(False, "OFFLINE"))
                self.after(0, lambda: self._set_log(f"healthz failed: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def apply_interval(self) -> None:
        minutes = self._minutes()
        self._sync_client()

        def work() -> None:
            try:
                data = self.client.set_interval(minutes)
                self.after(
                    0,
                    lambda: self._set_log(
                        f"已设置服务端定时校验: {data.get('scan_interval_minutes')} 分钟"
                    ),
                )
                self.after(0, self.refresh_status)
            except Exception as e:  # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("设置失败", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def do_scan(self) -> None:
        self._sync_client()
        self._set_log("正在 force scan…")

        def work() -> None:
            try:
                data = self.client.force_scan()
                text = json.dumps(data, ensure_ascii=False, indent=2)
                self.after(0, lambda: self._append("--- force scan ---\n" + text + "\n"))
                self.after(0, lambda: self._set_log("scan 完成"))
            except Exception as e:  # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("扫描失败", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def do_suggest(self) -> None:
        q = self.q_text.get("1.0", "end").strip()
        if not q:
            messagebox.showwarning("提示", "请先填写模拟问题")
            return
        group = self.group_var.get().strip() or "【JS】GUI模拟群"
        self._sync_client()
        self._set_log("正在生成建议（可能需 10–60 秒）…")

        def work() -> None:
            try:
                data = self.client.suggest(q, group_name=group)
                block = (
                    f"=== 模拟问答 ===\n"
                    f"群: {data.get('group_name')}\n"
                    f"问: {data.get('question')}\n"
                    f"来源: {data.get('source')}\n\n"
                    f"{data.get('suggestion')}\n"
                )
                self.after(0, lambda: self._append(block))
                self.after(0, lambda: self._set_log(f"suggest ok source={data.get('source')}"))
            except Exception as e:  # noqa: BLE001
                self.after(0, lambda: messagebox.showerror("模拟失败", str(e)))
                self.after(0, lambda: self._set_log(f"suggest failed: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def clear_out(self) -> None:
        self.out.delete("1.0", "end")
        self.out.insert("1.0", "等待指令…\n")

    def toggle_gui_timer(self) -> None:
        if self._auto_job is not None:
            try:
                self.after_cancel(self._auto_job)
            except Exception:  # noqa: BLE001
                pass
            self._auto_job = None
        if self.gui_auto.get():
            self._gui_tick()

    def _gui_tick(self) -> None:
        if not self.gui_auto.get():
            return
        minutes = max(1, self._minutes())
        self._set_log(f"GUI 计时：{minutes} 分钟后提醒")
        self._auto_job = self.after(minutes * 60 * 1000, self._gui_fire)

    def _gui_fire(self) -> None:
        self._set_log("GUI 计时到点")
        if messagebox.askyesno("定时提醒", "校验间隔已到，是否立即 force scan？"):
            self.do_scan()
        self._gui_tick()


def main() -> None:
    try:
        app = App()
    except tk.TclError as e:
        print(f"[error] 无法启动桌面 GUI（Tcl/Tk）: {e}")
        print("可改用浏览器版: python app/web_ui.py")
        raise SystemExit(1) from e
    app.mainloop()


if __name__ == "__main__":
    main()
