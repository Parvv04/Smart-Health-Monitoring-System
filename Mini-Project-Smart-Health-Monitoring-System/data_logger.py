# data_logger.py - FIXED VERSION
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
        """Ensure CSV has correct headers, migrate if needed"""
        if not os.path.exists(self.csv_path):
            # Create new file with correct headers
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "ear", "total_blinks", "blinks_last_min", 
                    "neck_angle", "back_angle"
                ])
            print("✅ New log file created with updated headers")
        else:
            # Check if file needs migration
            try:
                with open(self.csv_path, "r", newline="") as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    
                    if headers and len(headers) == 7:  # Old format
                        print("🔄 Migrating old log file to new format...")
                        self._migrate_old_format()
                    elif headers and len(headers) == 8:  # Already correct
                        print("✅ Log file has correct format")
                    else:
                        print("⚠️ Unknown log format, creating new file")
                        self._create_new_file()
            except Exception as e:
                print(f"⚠️ Error checking log file: {e}, creating new file")
                self._create_new_file()

    def _migrate_old_format(self):
        """Migrate from old 7-column format to new 8-column format"""
        try:
            # Read old data
            with open(self.csv_path, "r", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Create backup
            backup_path = self.csv_path + ".backup"
            with open(backup_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            
            # Write new format
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                # New headers
                writer.writerow([
                    "timestamp", "ear", "total_blinks", "blinks_last_min", 
                    "neck_angle", "back_angle"
                ])
                
                # Migrate old rows, adding default back_angle
                for row in rows[1:]:  # Skip old header
                    if len(row) >= 7:
                        new_row = row[:5] + [0.0] + row[5:]  # Insert back_angle=0.0
                        writer.writerow(new_row)
            
            print("✅ Successfully migrated log file to new format")
            
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
                "neck_angle", "back_angle"
            ])
        print("✅ Created new log file")

    def log(self, ear, total_blinks, blinks_last_min, neck_angle, back_angle, alert):
        ts = datetime.now().isoformat()

        # detect slouch event
        slouch_flag = 1 if alert and any(keyword in str(alert).lower() for keyword in ["posture", "neck", "back", "slouch", "hunch"]) else 0

        # always log all values
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                round(ear or 0, 3),
                int(total_blinks or 0),
                round(blinks_last_min or 0, 2),
                round(neck_angle or 0, 2),
                round(back_angle or 0, 2)
            ])
        print(f"✅ Data logged: Neck={neck_angle:.1f}°, Back={back_angle:.1f}°")

        if self.firebase_ref:
            try:
                payload = {
                    "timestamp": ts,
                    "ear": ear,
                    "total_blinks": total_blinks,
                    "blinks_last_min": blinks_last_min,
                    "neck_angle": neck_angle,
                    "back_angle": back_angle,
                }
                push_log(self.firebase_ref, payload)
            except Exception as e:
                print("Firebase push failed:", e)