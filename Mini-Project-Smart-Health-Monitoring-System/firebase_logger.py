# firebase_logger.py - ENHANCED VERSION
import firebase_admin
from firebase_admin import credentials, db
import os
import json
from datetime import datetime
import csv

def init_firebase(json_path="firebase_config.json",
                db_url="https://smart-health-monitor-29524-default-rtdb.asia-southeast1.firebasedatabase.app/"):
    """Initializes Firebase app and returns a reference to /health_logs node."""
    if not os.path.exists(json_path):
        print(f"❌ Firebase config not found at: {json_path}")
        print("Please download your Firebase service account key and save as 'firebase_config.json'")
        return None

    try:
        # Initialize only once
        if not firebase_admin._apps:
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred, {
                "databaseURL": db_url,
                "databaseAuthVariableOverride": None
            })
            print("✅ Firebase initialized successfully")

        ref = db.reference("/health_logs")
        
        # Test connection
        test_ref = ref.push({
            "test_connection": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Connection test from Smart Health Monitor"
        })
        print("✅ Firebase connection test successful")
        
        return ref
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return None

def push_log(ref, payload):
    """Pushes one log entry to Firebase with error handling."""
    if ref is None:
        print("⚠️ Firebase not available - skipping cloud log")
        return False
        
    try:
        # Add timestamp if not present
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.now().isoformat()
            
        result = ref.push(payload)
        print(f"✅ Data logged to cloud: {payload['timestamp']}")
        return True
    except Exception as e:
        print(f"❌ Firebase push failed: {e}")
        return False

# Enhanced DataLogger with better cloud handling
class DataLogger:
    def __init__(self, csv_path="logs/health_log.csv"):
        os.makedirs("logs", exist_ok=True)
        self.csv_path = csv_path
        
        # Create CSV with headers if not exists
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "ear", "total_blinks", "blinks_last_min", 
                    "posture_angle", "alert"
                ])
            print("✅ New log file created")
        
        # Initialize Firebase
        self.firebase_ref = init_firebase()
        if self.firebase_ref:
            print("✅ Cloud logging ENABLED")
        else:
            print("⚠️ Cloud logging DISABLED - using local storage only")

    def log(self, ear, total_blinks, blinks_last_min, posture_angle, alert):
        timestamp = datetime.now().isoformat()
        slouch_flag = 1 if alert and "Bad posture" in alert else 0

        # Log to CSV (local storage)
        try:
            with open(self.csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    round(ear or 0, 3),
                    int(total_blinks or 0),
                    int(blinks_last_min or 0),
                    round(posture_angle or 0, 1),

                ])
            print(f"✅ Data logged locally: {timestamp}")
        except Exception as e:
            print(f"❌ Local log failed: {e}")

        # Log to Firebase (cloud storage)
        if self.firebase_ref:
            payload = {
                "timestamp": timestamp,
                "ear": ear,
                "total_blinks": total_blinks,
                "blinks_last_min": blinks_last_min,
                "posture_angle": posture_angle,
                "device": "laptop_camera",
                "alert": alert if alert else "None"
            }
            push_log(self.firebase_ref, payload)