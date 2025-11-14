# health_report.py - UPDATED VERSION
import os
import pandas as pd
import customtkinter as ctk
from datetime import datetime

LOG_PATH = "logs/health_log.csv"

def calculate_report():
    if not os.path.exists(LOG_PATH):
        return {"error": "No data file found."}

    try:
        df = pd.read_csv(LOG_PATH, encoding="latin1")
    except Exception as e:
        return {"error": f"Failed to read log file: {e}"}

    if df.empty or "timestamp" not in df.columns:
        return {"error": "No valid data to show."}

    # Clean data
    df = df.dropna(subset=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # Basic metrics
    total_blinks = df["total_blinks"].iloc[-1] if not df.empty else 0
    blinks_last_min = df["blinks_last_min"].iloc[-1] if not df.empty else 0
    total_logs = len(df)

    # Approx screen time
    if len(df) > 1:
        duration = (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]).total_seconds()
    else:
        duration = 0
    screen_time_hours = duration / 3600

    # Fatigue estimation
    fatigue_level = "Low"
    if blinks_last_min < 10:
        fatigue_level = "High"
    elif 10 <= blinks_last_min <= 15:
        fatigue_level = "Moderate"

    # Posture analysis using both neck and back angles
    if "neck_angle" in df.columns and "back_angle" in df.columns:
        # Count slouches based on slouch_flag
        if "slouch_flag" in df.columns:
            df["slouch_flag"] = pd.to_numeric(df["slouch_flag"], errors="coerce").fillna(0)
            slouch_count = int(df["slouch_flag"].sum())
        else:
            # Fallback: count alerts with posture keywords
            alert_col = "alert"
            keywords = ["bad posture", "posture", "slouch", "sit straight", "slouching", "neck", "back", "hunch"]
            def row_has_posture(val):
                try:
                    s = str(val).lower()
                except Exception:
                    return False
                return any(k in s for k in keywords)

            slouch_count = int(df[alert_col].apply(row_has_posture).sum())
        
        slouch_rate = (slouch_count / len(df)) * 100 if len(df) > 0 else 0
        
        # Average angles for report
        avg_neck_angle = df["neck_angle"].mean() if not df["neck_angle"].isna().all() else 0
        avg_back_angle = df["back_angle"].mean() if not df["back_angle"].isna().all() else 0
    else:
        slouch_count = 0
        slouch_rate = 0
        avg_neck_angle = 0
        avg_back_angle = 0

    # Dummy values for other fields
    eye_wetness = "Normal"
    light_level = "Balanced"
    disease_risk = "Low"

    # Summary message
    if fatigue_level == "High" or slouch_rate > 20:
        message = "⚠️ You need to take better care of yourself!"
    elif fatigue_level == "Moderate" or slouch_rate > 10:
        message = "🙂 Doing okay, but take a short break soon."
    else:
        message = "💪 Good job! You're maintaining healthy habits."

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "screen_time": f"{screen_time_hours:.2f} hrs",
        "total_blinks": int(total_blinks),
        "blinks_per_min": round(blinks_last_min, 2),
        "fatigue_level": fatigue_level,
        "eye_wetness": eye_wetness,
        "light_level": light_level,
        "disease_risk": disease_risk,
        "avg_neck_angle": f"{avg_neck_angle:.1f}°",
        "avg_back_angle": f"{avg_back_angle:.1f}°",
        "message": message
    }

def show_report():
    stats = calculate_report()

    app = ctk.CTk()
    app.title("Smart Health Report")
    app.geometry("450x550")  # Slightly larger to accommodate new fields

    frame = ctk.CTkFrame(app)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(frame, text="🩺 Smart Health Report", font=("Helvetica", 20, "bold")).pack(pady=(10, 20))

    if "error" in stats:
        ctk.CTkLabel(frame, text=stats["error"], text_color="red").pack(pady=20)
        app.mainloop()
        return

    for key, label in [
        ("date", "📅 Date"),
        ("screen_time", "💻 Screen Time"),
        ("total_blinks", "👁️ Total Blinks"),
        ("blinks_per_min", "⏱️ Blinks/min"),
        ("fatigue_level", "😴 Fatigue Level"),
        ("eye_wetness", "💧 Eye Wetness"),
        ("light_level", "💡 Light Level"),
        ("disease_risk", "⚠️ Disease Risk"),
        ("avg_neck_angle", "📐 Avg Neck Angle"),
        ("avg_back_angle", "📏 Avg Back Angle"),
    ]:
        ctk.CTkLabel(frame, text=f"{label}: {stats[key]}", font=("Helvetica", 14)).pack(anchor="w", padx=10, pady=3)

    ctk.CTkLabel(frame, text="", height=10).pack()
    ctk.CTkLabel(frame, text=stats["message"], font=("Helvetica", 15, "bold"), wraplength=300).pack(pady=10)

    ctk.CTkButton(frame, text="Close", command=app.destroy).pack(pady=15)
    app.mainloop()