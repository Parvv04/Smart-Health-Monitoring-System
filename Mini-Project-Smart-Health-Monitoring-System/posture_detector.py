# posture_detector.py - IMPROVED BACK ANGLE DETECTION
import mediapipe as mp
import math
import time
from collections import deque

mp_pose = mp.solutions.pose

class PostureDetector:
    def __init__(self, neck_threshold=15.0, back_threshold=1.0, slouch_duration=2., calibration_time=3.0):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            model_complexity=1
        )
        self.neck_threshold = neck_threshold  # Neck forward bending
        self.back_threshold = back_threshold  # Upper back curvature  
        self.slouch_duration = slouch_duration
        self.calibration_time = calibration_time
        self.slouch_start = None
        self.calibrated = False
        self.calibration_start = time.time()
        
    def calculate_neck_angle(self, landmarks, image_w, image_h):
        """Calculate neck forward bending using nose and shoulders"""
        try:
            # Use nose and shoulders - most reliable landmarks
            nose = landmarks[0]              # Nose tip
            left_shoulder = landmarks[11]    # Left shoulder
            right_shoulder = landmarks[12]   # Right shoulder
            
            # Calculate shoulder midpoint
            shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
            shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
            
            # Convert to pixel coordinates
            nose_x = nose.x * image_w
            nose_y = nose.y * image_h
            shoulder_x = shoulder_mid_x * image_w
            shoulder_y = shoulder_mid_y * image_h
            
            # Calculate horizontal and vertical distances
            horizontal_dist = abs(nose_x - shoulder_x)  # How much head is forward
            vertical_dist = abs(nose_y - shoulder_y)    # How much head is above shoulders
            
            # Avoid division by zero
            if vertical_dist < 1:
                vertical_dist = 1
                
            # Calculate angle: arctan(horizontal/vertical)
            # More horizontal distance = larger angle = more neck bending
            angle_rad = math.atan(horizontal_dist / vertical_dist)
            angle_deg = math.degrees(angle_rad)
            
            return angle_deg
            
        except Exception as e:
            print(f"Neck angle calculation error: {e}")
            return 0.0

    def calculate_back_angle(self, landmarks, image_w, image_h):
        """Calculate spine bending using shoulders and hips (most reliable)"""
        try:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            # Midpoints
            shoulder_x = (left_shoulder.x + right_shoulder.x) / 2 * image_w
            shoulder_y = (left_shoulder.y + right_shoulder.y) / 2 * image_h

            hip_x = (left_hip.x + right_hip.x) / 2 * image_w
            hip_y = (left_hip.y + right_hip.y) / 2 * image_h

            # Vertical vector (hip to shoulder)
            dx = shoulder_x - hip_x
            dy = shoulder_y - hip_y

            # Angle of spine from vertical
            angle_rad = math.atan2(abs(dx), abs(dy))
            angle_deg = math.degrees(angle_rad)

            return angle_deg  # 0° = straight, higher = more bend

        except:
            return 0.0


    def process(self, image_rgb, image_w, image_h):
        results = self.pose.process(image_rgb)
        alert = None
        neck_angle = 0.0
        back_angle = 0.0

        if results.pose_landmarks:
            neck_angle = self.calculate_neck_angle(results.pose_landmarks.landmark, image_w, image_h)
            back_angle = self.calculate_back_angle(results.pose_landmarks.landmark, image_w, image_h)
        
            if not self.calibrated:
                if time.time() - self.calibration_start < self.calibration_time:
                    print(f"📏 Calibrating... Neck: {neck_angle:.1f}° | Back: {back_angle:.1f}°")
                else:
                    self.calibrated = True
                    print(f"✅ Calibration complete! Now monitoring...")

            else:
                # Debug info
                print(f"📐 Neck: {neck_angle:.1f}° (>{self.neck_threshold}?) | Back: {back_angle:.1f}° (>{self.back_threshold}?)")
            
                neck_slouching = neck_angle > self.neck_threshold
                back_slouching = back_angle > self.back_threshold
                
                is_slouching = neck_slouching or back_slouching
            
                if is_slouching:
                    if self.slouch_start is None:
                        self.slouch_start = time.time()
                        # Determine slouch type
                        if neck_slouching and back_slouching:
                            slouch_type = "neck and back"
                        elif neck_slouching:
                            slouch_type = "neck" 
                        else:
                            slouch_type = "back"
                        print(f"⚠️ {slouch_type.title()} slouch detected! Starting timer...")
                
                    # Check if slouch has lasted long enough
                    elif time.time() - self.slouch_start >= self.slouch_duration:
                        # IMPROVED ALERT MESSAGES - More descriptive
                        if neck_slouching and back_slouching:
                            alert = f"POSTURE: Straighten your neck and back! (Neck: {neck_angle:.1f}°, Back: {back_angle:.1f}°)"
                        elif neck_slouching:
                            alert = f"POSTURE: Neck strain! Sit upright. (Angle: {neck_angle:.1f}°)"
                        else:
                            alert = f"POSTURE: Hunched back! Straighten spine. (Angle: {back_angle:.1f}°)"
                        print(f"🚨 ALERT TRIGGERED: {alert}")
                else:
                    if self.slouch_start is not None:
                        print(f"✅ Posture corrected - resetting timer")
                    self.slouch_start = None
    
        return neck_angle, back_angle, alert

    def close(self):
        """Close the MediaPipe Pose instance to release resources"""
        if hasattr(self, 'pose'):
            self.pose.close()
            print("✅ PostureDetector closed successfully")