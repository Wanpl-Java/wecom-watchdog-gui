"""WeCom Watchdog Console — interval + simulate Q&A."""
from __future__ import annotations

import json
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional

_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

try:
    import customtkinter as ctk

    USE_CTK = True
except ImportError:  # noqa: BLE001
    USE_CTK = False

from client import WatchdogClient

PRESETS = [("5 分钟", 5), ("10 分钟", 10), ("15 分钟", 15), ("30 分钟", 30)]
SAMPLE_QS = [
    "JumpServer远程应用发布机怎么部署",
    "登录提示配置文件有问题无法登录 DOMAINS",
    "Tinker 离线怎么办",
    "资产连接超时怎么排查",
]


class App:
    def __init__(self) -> None:
        if USE_CTK:
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
            self._Frame = ctk.CTkFrame
            self._Label = ctk.CTkLabel
            self._Entry = ctk.CTkEntry
            self._Button = ctk.CTkButton
            self._Text = ctk.CTkTextbox
            self._Option = ctk.CTkOptionMenu
            self._Check = ctk.CTkCheckBox
        else:
            self.root = tk.Tk()
            self._Frame = ttk.Frame
            self._Label = ttk.Label
            self._Entry = ttk.Entry
            self._Button = ttk.Button
            self._Text = None  # use tk.Text
            self._Option = None
            self._Check = None

        self.root.title("WeCom Watchdog Console")
        self.root.geometry("960x720")
        self.root.minsize(800, 600)

        self.client = WatchdogClient()
        self._auto_job: Optional[str] = None
        self._build()
        self.root.after(300, self.refresh_status)

    def _build(self) -> None:
        pad = {"padx": 12, "pady": 8}
        top = self._Frame(self.root)
        top.pack(fill="x", **pad)

        self._Label(top, text="Watchdog 地址").grid(row=0, column=0, sticky="w")
        self.base_var = tk.StringVar(value="http://127.0.0.1:8092")
        if USE_CTK:
            self.base_entry = self._Entry(top, textvariable=self.base_var, width=360)
        else:
            self.base_entry = self._Entry(top, textvariable=self.base_var, width=48)
        self.base_entry.grid(row=0, column=1, sticky="we", padx=8)
        self._Button(top, text="检测连接", command=self.refresh_status).grid(row=0, column=2)

        self.status_var = tk.StringVar(value="状态：未检测")
        self._Label(top, textvariable=self.status_var).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )
        top.columnconfigure(1, weight=1)

        # --- interval ---
        box = self._Frame(self.root)
        box.pack(fill="x", **pad)
        self._Label(box, text="定时校验间隔").grid(row=0, column=0, sticky="w")

        self.interval_choice = tk.StringVar(value="5 分钟")
        labels = [p[0] for p in PRESETS] + ["自定义"]
        if USE_CTK:
            self._Option(box, values=labels, variable=self.interval_choice, width=140).grid(
                row=0, column=1, padx=8
            )
        else:
            ttk.Combobox(box, textvariable=self.interval_choice, values=labels, width=14).grid(
                row=0, column=1, padx=8
            )

        self.custom_min = tk.StringVar(value="5")
        self._Label(box, text="自定义(分钟)").grid(row=0, column=2, sticky="e")
        if USE_CTK:
            self._Entry(box, textvariable=self.custom_min, width=80).grid(row=0, column=3, padx=8)
        else:
            self._Entry(box, textvariable=self.custom_min, width=8).grid(row=0, column=3, padx=8)

        self._Button(box, text="应用到 Watchdog", command=self.apply_interval).grid(
            row=0, column=4, padx=8
        )
        self._Button(box, text="立即扫描", command=self.do_scan).grid(row=0, column=5)

        self.gui_auto = tk.BooleanVar(value=False)
        if USE_CTK:
            self._Check(
                box,
                text="GUI 侧同步计时提醒（不替代服务端调度）",
                variable=self.gui_auto,
                command=self.toggle_gui_timer,
            ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))
        else:
            ttk.Checkbutton(
                box,
                text="GUI 侧同步计时提醒（不替代服务端调度）",
                variable=self.gui_auto,
                command=self.toggle_gui_timer,
            ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))

        # --- simulate ---
        mid = self._Frame(self.root)
        mid.pack(fill="both", expand=True, **pad)
        self._Label(mid, text="模拟客户问题").pack(anchor="w")

        self.q_var = tk.StringVar(value=SAMPLE_QS[0])
        row = self._Frame(mid)
        row.pack(fill="x", pady=4)
        if USE_CTK:
            self._Option(row, values=SAMPLE_QS, variable=self.q_var, width=420, command=self._on_sample).pack(
                side="left", fill="x", expand=True
            )
        else:
            cb = ttk.Combobox(row, textvariable=self.q_var, values=SAMPLE_QS, width=70)
            cb.pack(side="left", fill="x", expand=True)
            cb.bind("<<ComboboxSelected>>", lambda _e: self._on_sample(self.q_var.get()))

        self.group_var = tk.StringVar(value="【JS】GUI模拟群")
        g = self._Frame(mid)
        g.pack(fill="x", pady=4)
        self._Label(g, text="模拟群名").pack(side="left")
        if USE_CTK:
            self._Entry(g, textvariable=self.group_var, width=280).pack(side="left", padx=8)
        else:
            self._Entry(g, textvariable=self.group_var, width=36).pack(side="left", padx=8)

        self._Label(mid, text="自定义问题（可编辑）").pack(anchor="w", pady=(8, 0))
        if USE_CTK:
            self.q_text = self._Text(mid, height=6)
            self.q_text.pack(fill="x")
            self.q_text.insert("1.0", SAMPLE_QS[0])
        else:
            self.q_text = tk.Text(mid, height=6, wrap="word")
            self.q_text.pack(fill="x")
            self.q_text.insert("1.0", SAMPLE_QS[0])

        btns = self._Frame(mid)
        btns.pack(fill="x", pady=8)
        self._Button(btns, text="发送模拟问答（生成建议）", command=self.do_suggest).pack(
            side="left", padx=(0, 8)
        )
        self._Button(btns, text="清空输出", command=self.clear_out).pack(side="left")

        self._Label(mid, text="输出").pack(anchor="w")
        if USE_CTK:
            self.out = self._Text(mid, height=18)
            self.out.pack(fill="both", expand=True)
        else:
            self.out = tk.Text(mid, height=18, wrap="word")
            self.out.pack(fill="both", expand=True)

        self.log_var = tk.StringVar(value="")
        self._Label(self.root, textvariable=self.log_var).pack(anchor="w", padx=12, pady=(0, 10))

    def _on_sample(self, value: str) -> None:
        self.q_text.delete("1.0", "end")
        self.q_text.insert("1.0", value)

    def _minutes(self) -> int:
        choice = self.interval_choice.get()
        for label, m in PRESETS:
            if choice == label:
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

    def refresh_status(self) -> None:
        self._sync_client()

        def work() -> None:
            try:
                data = self.client.healthz()
                msg = (
                    f"状态：在线 | mode={data.get('workbuddy_mode')} | "
                    f"scan={data.get('scan_interval_minutes')}min | "
                    f"source={data.get('message_source')}"
                )
                self.root.after(0, lambda: self.status_var.set(msg))
                self.root.after(0, lambda: self._set_log("healthz ok"))
            except Exception as e:  # noqa: BLE001
                self.root.after(0, lambda: self.status_var.set(f"状态：离线 — {e}"))
                self.root.after(0, lambda: self._set_log(f"healthz failed: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def apply_interval(self) -> None:
        minutes = self._minutes()
        self._sync_client()

        def work() -> None:
            try:
                data = self.client.set_interval(minutes)
                self.root.after(
                    0,
                    lambda: self._set_log(
                        f"已设置服务端定时校验: {data.get('scan_interval_minutes')} 分钟"
                    ),
                )
                self.root.after(0, self.refresh_status)
            except Exception as e:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("设置失败", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def do_scan(self) -> None:
        self._sync_client()
        self._set_log("正在 force scan…")

        def work() -> None:
            try:
                data = self.client.force_scan()
                text = json.dumps(data, ensure_ascii=False, indent=2)
                self.root.after(0, lambda: self._append("--- force scan ---\n" + text + "\n"))
                self.root.after(0, lambda: self._set_log("scan 完成"))
            except Exception as e:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("扫描失败", str(e)))

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
                self.root.after(0, lambda: self._append(block))
                self.root.after(0, lambda: self._set_log(f"suggest ok source={data.get('source')}"))
            except Exception as e:  # noqa: BLE001
                self.root.after(0, lambda: messagebox.showerror("模拟失败", str(e)))
                self.root.after(0, lambda: self._set_log(f"suggest failed: {e}"))

        threading.Thread(target=work, daemon=True).start()

    def clear_out(self) -> None:
        self.out.delete("1.0", "end")

    def toggle_gui_timer(self) -> None:
        if self._auto_job is not None:
            try:
                self.root.after_cancel(self._auto_job)
            except Exception:  # noqa: BLE001
                pass
            self._auto_job = None
        if self.gui_auto.get():
            self._gui_tick()

    def _gui_tick(self) -> None:
        if not self.gui_auto.get():
            return
        minutes = max(1, self._minutes())
        self._set_log(f"GUI 计时：{minutes} 分钟后提醒（可点立即扫描）")
        self._auto_job = self.root.after(minutes * 60 * 1000, self._gui_fire)

    def _gui_fire(self) -> None:
        self._set_log("GUI 计时到点，可执行立即扫描")
        if messagebox.askyesno("定时提醒", "校验间隔已到，是否立即 force scan？"):
            self.do_scan()
        self._gui_tick()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
