# data_logger.py
import os
import csv
import time
from datetime import datetime
from firebase_logger import init_firebase, push_log

LOG_DIR = "logs"
CSV_PATH = os.path.join(LOG_DIR, "health_log.csv")

class DataLogger:
    def __init__(self, csv_path=CSV_PATH):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.csv_path = csv_path
        
        self._ensure_csv_headers()
        
        self.firebase_ref = None
        if os.path.exists("firebase_config.json"):
            try:
                self.firebase_ref = init_firebase()
                print("✅ Connected to Firebase successfully")
            except Exception as e:
                print(f"⚠️ Note: Firebase logging disabled - {str(e)}")
        else:
            print("ℹ️ Note: Firebase logging disabled (no firebase_config.json found)")

    def _ensure_csv_headers(self):
        """Ensure CSV has correct headers with ALERT column"""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "ear", "total_blinks", "blinks_last_min", 
                    "neck_angle", "back_angle", "slouch_flag", "alert"
                ])
            print("✅ New log file created with ALERT column")
        else:
            try:
                with open(self.csv_path, "r", newline="") as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    
                    if headers and len(headers) < 8:  # Missing alert column
                        print("🔄 Migrating log file to include alert column...")
                        self._migrate_to_include_alert()
                    else:
                        print("✅ Log file has correct format")
            except Exception as e:
                print(f"⚠️ Error checking log file: {e}, creating new file")
                self._create_new_file()

    def _migrate_to_include_alert(self):
        """Migrate existing file to include alert column"""
        try:
            with open(self.csv_path, "r", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            backup_path = self.csv_path + ".backup"
            with open(backup_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "ear", "total_blinks", "blinks_last_min", 
                    "neck_angle", "back_angle", "slouch_flag", "alert"
                ])
                
                for row in rows[1:]:
                    if len(row) >= 6:
                        # Add missing columns with default values
                        new_row = row[:6]  # Take first 6 columns
                        if len(new_row) < 7:
                            new_row.append(0)  # Add slouch_flag
                        if len(new_row) < 8:
                            new_row.append("None")  # Add alert
                        writer.writerow(new_row)
            
            print("✅ Successfully migrated log file")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}, creating new file")
            self._create_new_file()

    def _create_new_file(self):
        """Create a new log file with correct headers"""
        try:
            os.remove(self.csv_path)
        except:
            pass
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "ear", "total_blinks", "blinks_last_min", 
                "neck_angle", "back_angle", "slouch_flag", "alert"
            ])
        print("✅ Created new log file")

    # In data_logger.py (Focus on the log method)

    def log(self, ear, total_blinks, blinks_last_min, neck_angle, back_angle, alert):
        ts = datetime.now().isoformat()

        # The issue is how 'alert' is received from the main loop. 
        # Assuming 'alert' is received correctly (e.g., "POSTURE: Neck strain!...")
    
        # IMPROVED SLOUCH DETECTION - Keep this as is, it's correct
        slouch_keywords = [
            "posture", "neck", "back", "slouch", "hunch", "strain", 
            "straighten", "spine", "hunched", "bent"
        ]

        has_slouch_alert = False
        # Only process if alert is not None and not the string "None" or "nan"
        if alert and str(alert).lower() != "none" and str(alert).lower() != "nan":
            alert_lower = str(alert).lower()
            has_slouch_alert = any(keyword in alert_lower for keyword in slouch_keywords)
            # The line below correctly sets slouch_flag to 1 if a posture alert is detected
            # This is how slouch_flag gets set for the CSV and Report
        
        slouch_flag = 1 if has_slouch_alert else 0

        # Ensure alert is not NaN/None for saving
        alert_to_save = alert if (alert and str(alert).lower() != "nan") else "None"
    
        # ... (Rest of the CSV and Firebase logging logic remains the same) ...
    
        # Log to CSV
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                round(ear or 0, 3),
                int(total_blinks or 0),
                round(blinks_last_min or 0, 2),
                round(neck_angle or 0, 2),
                round(back_angle or 0, 2),
                slouch_flag,  # <--- THIS IS NOW SET TO 1 if a posture alert is in 'alert'
                alert_to_save
            ])
    
    # ... (Firebase logging logic remains the same) ...
        # Log to Firebase
        if self.firebase_ref:
            try:
                payload = {
                    "timestamp": ts,
                    "ear": ear,
                    "total_blinks": total_blinks,
                    "blinks_last_min": blinks_last_min,
                    "neck_angle": neck_angle,
                    "back_angle": back_angle,
                    "slouch_flag": slouch_flag,
                    "alert": alert_to_save
                }
                push_log(self.firebase_ref, payload)
            except Exception as e:
                print("Firebase push failed:", e)