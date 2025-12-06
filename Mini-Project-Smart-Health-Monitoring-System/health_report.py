import os
import pandas as pd
import customtkinter as ctk
from datetime import datetime

LOG_PATH = "logs/health_log.csv"

def calculate_report():
    if not os.path.exists(LOG_PATH):
        return {"error": "No data file found."}

    try:
        df = pd.read_csv(LOG_PATH)
    except Exception as e:
        return {"error": f"Failed to read log file: {e}"}

    if df.empty or "timestamp" not in df.columns:
        return {"error": "No valid data to show."}

    # Clean data
    df = df.dropna(subset=["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # Basic metrics
    total_blinks = df["total_blinks"].iloc[-1] if not df.empty and "total_blinks" in df.columns else 0
    blinks_last_min = df["blinks_last_min"].iloc[-1] if not df.empty and "blinks_last_min" in df.columns else 0
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

    # IMPROVED Posture analysis - FIXED SLOUCH RATE CALCULATION
    slouch_count = 0
    avg_neck_angle = 0
    avg_back_angle = 0
    
    if "slouch_flag" in df.columns:
        df["slouch_flag"] = pd.to_numeric(df["slouch_flag"], errors="coerce").fillna(0)
        slouch_count = int(df["slouch_flag"].sum())
    
    if "neck_angle" in df.columns:
        avg_neck_angle = df["neck_angle"].mean() if not df["neck_angle"].isna().all() else 0
    
    if "back_angle" in df.columns:
        avg_back_angle = df["back_angle"].mean() if not df["back_angle"].isna().all() else 0
    
    # Calculate slouch rate properly
    slouch_rate = (slouch_count / len(df)) * 100 if len(df) > 0 else 0

    # Dummy values for other fields
    eye_wetness = "Normal"
    light_level = "Balanced"
    disease_risk = "Low"

    # Summary message - USING THE SLOUCH RATE PROPERLY
    if fatigue_level == "High" or slouch_rate > 20:
        message = "⚠️ You need to take better care of yourself! Consider taking breaks and improving posture."
    elif fatigue_level == "Moderate" or slouch_rate > 10:
        message = "🙂 Doing okay, but take a short break soon and check your sitting posture."
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
        "slouching_rate": f"{slouch_rate:.1f}%",  # THIS WILL NOW SHOW CORRECTLY
        "slouch_count": slouch_count,  # Added for debugging
        "total_logs": total_logs,  # Added for debugging
        "avg_neck_angle": f"{avg_neck_angle:.1f}°",
        "avg_back_angle": f"{avg_back_angle:.1f}°",
        "message": message
    }

def show_report():
    stats = calculate_report()

    app = ctk.CTk()
    app.title("Smart Health Report")
    app.geometry("450x550")

    frame = ctk.CTkFrame(app)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(frame, text="🩺 Smart Health Report", font=("Helvetica", 20, "bold")).pack(pady=(10, 20))

    if "error" in stats:
        ctk.CTkLabel(frame, text=stats["error"], text_color="red").pack(pady=20)
        app.mainloop()
        return

    # Display all metrics including slouching rate
    for key, label in [
        ("date", "📅 Date"),
        ("screen_time", "💻 Screen Time"),
        ("total_blinks", "👁️ Total Blinks"),
        ("blinks_per_min", "⏱️ Blinks/min"),
        ("fatigue_level", "😴 Fatigue Level"),
        ("slouching_rate", "🧍 Slouching Rate"),
        ("avg_neck_angle", "📐 Avg Neck Angle"),
        ("avg_back_angle", "📏 Avg Back Angle"),
    ]:
        ctk.CTkLabel(frame, text=f"{label}: {stats[key]}", font=("Helvetica", 14)).pack(anchor="w", padx=10, pady=3)

    # Optional: Show debug info (you can remove this in production)
    ctk.CTkLabel(frame, text=f"Debug: {stats['slouch_count']} slouches in {stats['total_logs']} records", 
                font=("Helvetica", 10), text_color="gray").pack(anchor="w", padx=10, pady=2)

    ctk.CTkLabel(frame, text="", height=10).pack()
    ctk.CTkLabel(frame, text=stats["message"], font=("Helvetica", 15, "bold"), wraplength=400).pack(pady=10)

    ctk.CTkButton(frame, text="Close", command=app.destroy).pack(pady=15)
    app.mainloop()