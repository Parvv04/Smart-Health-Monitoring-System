import tkinter as tk
from tkinter import ttk
import threading

def show_notification(title, message, on_ok=None, on_view_report=None):
    def run_popup():
        popup = tk.Toplevel()  # instead of Tk()
        popup.title(title)
        popup.geometry("400x200")
        popup.configure(bg="#ffcccc")
        popup.resizable(False, False)

        tk.Label(
            popup,
            text=title,
            font=("Segoe UI", 14, "bold"),
            bg="#ffcccc",
            fg="#900"
        ).pack(pady=(20, 10))

        tk.Label(
            popup,
            text=message,
            font=("Segoe UI", 11),
            bg="#ffcccc",
            wraplength=350
        ).pack(pady=(0, 20), padx=20)

        btn_frame = tk.Frame(popup, bg="#ffcccc")
        btn_frame.pack()

        def ok_action():
            if on_ok:
                on_ok()
            popup.destroy()

        ttk.Button(btn_frame, text="OK", command=ok_action).pack(side="left", padx=10)

        if on_view_report:
            def open_report():
                popup.destroy()
                # schedule show_report on main thread
                popup.after(100, on_view_report)

            ttk.Button(btn_frame, text="View Report", command=open_report).pack(side="left", padx=10)

        popup.attributes('-topmost', True)
        popup.after(100, popup.bell)
        popup.after(5000, lambda: popup.destroy() if popup.winfo_exists() else None)

    # Always create popup inside main thread via after()
    root = tk._default_root
    if root and root.winfo_exists():
        root.after(0, run_popup)
    else:
        t = threading.Thread(target=run_popup, daemon=True)
        t.start()
