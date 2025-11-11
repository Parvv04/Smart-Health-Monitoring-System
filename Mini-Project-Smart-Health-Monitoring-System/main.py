#main.py
import cv2
import time
import os
import csv
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from blink_detector import BlinkDetector
from posture_detector import PostureDetector
from data_logger import DataLogger
from ui_notifications import show_notification
from health_report import show_report

last_posture_alert = 0
last_drowsy_alert = 0
ALERT_COOLDOWN = 8  # seconds before showing the same type of alert again


def preload_models():
    from blink_detector import BlinkDetector
    from posture_detector import PostureDetector
    global blink, posture
    blink = BlinkDetector()
    posture = PostureDetector()
    print("✅ Models preloaded")

threading.Thread(target=preload_models, daemon=True).start()

# ===========================================================
# OVERLAY DRAW FUNCTION
# ===========================================================
def draw_overlay(frame, ear, blinks_total, blinks_min, neck_angle, back_angle, alerts):
    cv2.putText(frame, f"EAR: {ear:.3f}" if ear else "EAR: --",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f"Total blinks: {blinks_total}",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Blinks/min: {blinks_min}",
                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Show both neck and back angles
    if neck_angle and neck_angle > 0:
        neck_text = f"Neck: {neck_angle:.1f}°"
        neck_color = (0, 255, 0) if neck_angle < 15 else (0, 255, 255) if neck_angle < 25 else (0, 0, 255)
        cv2.putText(frame, neck_text, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, neck_color, 2)
    
    if back_angle and back_angle > 0:
        back_text = f"Back: {back_angle:.1f}°"
        back_color = (0, 255, 0) if back_angle < 20 else (0, 255, 255) if back_angle < 30 else (0, 0, 255)
        cv2.putText(frame, back_text, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, back_color, 2)

    # Show alerts
    y = 180
    for a in alerts:
        cv2.putText(frame, f"ALERT: {a}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        y += 30
    
    return frame



# ===========================================================
# REPORT VIEWER
# ===========================================================
# in main.py (replace existing view_report)
def view_report():

    if not os.path.exists("logs/health_log.csv"):
        messagebox.showwarning("No Data", "No report found. Please start monitoring first.")
        return

    """Display the CSV health report in a new window."""
    LOG_PATH = "logs/health_log.csv"   # <- match DataLogger path

    try:
        with open(LOG_PATH, "r", newline="") as file:
            data = list(csv.reader(file))

        if len(data) <= 1:
            messagebox.showinfo("No data", "Log exists but no entries recorded yet.")
            return

        win = tk.Toplevel()
        win.title("Smart Health Monitoring Report")
        win.geometry("700x400")

        style = ttk.Style(win)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))
        style.configure("Treeview", font=("Segoe UI", 10))

        tree = ttk.Treeview(win, columns=("Time", "Alert"), show="headings", height=15)
        tree.heading("Time", text="Timestamp")
        tree.heading("Alert", text="Event / Alert")
        tree.column("Time", width=200, anchor="center")
        tree.column("Alert", width=450, anchor="w")

        for row in data[1:]:
            # guard against rows with fewer columns
            timestamp = row[0] if len(row) > 0 else ""
            alert = row[5] if len(row) > 5 else ""
            tree.insert("", "end", values=(timestamp, alert))

        tree.pack(padx=20, pady=20, fill="both", expand=True)

    except FileNotFoundError:
        messagebox.showerror("Error", "No report file found! Run the program first.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open report: {e}")


# ===========================================================
# MONITORING LOOP
# ===========================================================
# In your main.py - UPDATE THE POSTURE DETECTION PART
def run_monitoring():
    global last_posture_alert, last_drowsy_alert
    
    # Use the FIXED detectors
    blink = BlinkDetector()
    posture = PostureDetector()  # This now uses the fixed version
    logger = DataLogger()
    last_log = 0

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Cannot open webcam.")
        return

    print("✅ Monitoring started. Press Q to quit.")
    print("📏 Sit straight for 3 seconds to calibrate posture detection...")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process blink detection
            ear, total_blinks, blinks_min, blink_alert = blink.process(rgb, frame.shape[1], frame.shape[0])
            
            neck_angle, back_angle, posture_alert = posture.process(rgb, frame.shape[1], frame.shape[0])

            alerts = []
            current_time = time.time()
            
            # Handle blink alerts
            if blink_alert and (current_time - last_drowsy_alert > ALERT_COOLDOWN):
                alerts.append(blink_alert)
                show_notification(
                    "Drowsiness Detected",
                    blink_alert,
                    on_ok=lambda: print("User acknowledged drowsiness alert"),
                    on_view_report=show_report
                )
                last_drowsy_alert = current_time

            # Handle posture alerts (FIXED)
            if posture_alert and (current_time - last_posture_alert > ALERT_COOLDOWN):
                alerts.append(posture_alert)
                show_notification(
                    "Posture Alert",
                    posture_alert,
                    on_ok=lambda: print("User adjusted posture"),
                    on_view_report=show_report
                )
                last_posture_alert = current_time

            # Log data every 5 seconds
            if time.time() - last_log > 5:
                logger.log(ear, total_blinks, blinks_min, neck_angle, back_angle, "; ".join(alerts))
                last_log = time.time()

            # Draw overlay with FIXED posture angle display
            frame = draw_overlay(frame, ear or 0.0, total_blinks, blinks_min, neck_angle, back_angle, alerts)
            cv2.imshow("Smart Health Monitor", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        blink.close()
        posture.close()
        print("🛑 Monitoring stopped.")


def start_monitoring():
    """Launch monitoring in a background thread."""
    t = threading.Thread(target=run_monitoring, daemon=True)
    t.start()


# ===========================================================
# TKINTER MAIN WINDOW
# ===========================================================
root = tk.Tk()
root.title("Smart Health Monitoring System")
root.geometry("400x220")

ttk.Button(root, text="▶ Start Monitoring", command=start_monitoring).pack(pady=10)
ttk.Button(root, text="📄 View Report", command=view_report).pack(pady=10)
ttk.Button(root, text="❌ Exit", command=root.destroy).pack(pady=10)

tk.Label(root, text="Press 'Q' in camera window to stop monitoring.",
        fg="gray").pack(side="bottom", pady=10)

def on_close():
    print("🛑 Exiting app...")
    os._exit(0)  # force terminate all threads including camera

root.protocol("WM_DELETE_WINDOW", on_close)


root.mainloop()
