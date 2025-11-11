# posture_detector.py - IMPROVED BACK ANGLE DETECTION
import mediapipe as mp
import math
import time
from collections import deque

mp_pose = mp.solutions.pose

class PostureDetector:
    def __init__(self, neck_threshold=15.0, back_threshold=15.0, slouch_duration=2.0, calibration_time=3.0):
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
        """Calculate upper back curvature using shoulders and ears (no hips needed)"""
        try:
            # Use shoulders and ears to estimate back curvature
            # When back is straight: ears are above shoulders
            # When back is hunched: ears move forward relative to shoulders
            
            left_shoulder = landmarks[11]    # Left shoulder
            right_shoulder = landmarks[12]   # Right shoulder
            left_ear = landmarks[7]          # Left ear
            right_ear = landmarks[8]         # Right ear
            
            # Calculate midpoints
            shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
            shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
            ear_mid_x = (left_ear.x + right_ear.x) / 2
            ear_mid_y = (left_ear.y + right_ear.y) / 2
            
            # Convert to pixel coordinates
            shoulder_x = shoulder_mid_x * image_w
            shoulder_y = shoulder_mid_y * image_h
            ear_x = ear_mid_x * image_w
            ear_y = ear_mid_y * image_h
            
            # Calculate the forward projection of ears relative to shoulders
            # When sitting straight: ear_x ≈ shoulder_x
            # When hunched: ear_x > shoulder_x (ears forward of shoulders)
            forward_projection = ear_x - shoulder_x
            
            # Calculate vertical alignment
            vertical_alignment = ear_y - shoulder_y  # Should be negative when upright
            
            # Calculate back angle based on forward projection and vertical alignment
            # This gives us an estimate of how much the upper back is hunched
            if abs(vertical_alignment) < 1:
                vertical_alignment = 1 if vertical_alignment >= 0 else -1
                
            back_angle = math.degrees(math.atan(abs(forward_projection) / abs(vertical_alignment)))
            
            # Scale the angle to be more meaningful (0-30 degrees range)
            scaled_angle = back_angle * 3  # Scale factor to make it more sensitive
            
            return min(scaled_angle, 45)  # Cap at 45 degrees
            
        except Exception as e:
            print(f"Back angle calculation error: {e}")
            return 0.0

    def process(self, image_rgb, image_w, image_h):
        results = self.pose.process(image_rgb)
        alert = None
        neck_angle = 0.0
        back_angle = 0.0

        if results.pose_landmarks:
            # Calculate both angles
            neck_angle = self.calculate_neck_angle(results.pose_landmarks.landmark, image_w, image_h)
            back_angle = self.calculate_back_angle(results.pose_landmarks.landmark, image_w, image_h)
            
            # Calibration phase
            if not self.calibrated:
                if time.time() - self.calibration_start < self.calibration_time:
                    print(f"📏 Calibrating... Neck: {neck_angle:.1f}° | Back: {back_angle:.1f}°")
                else:
                    self.calibrated = True
                    print(f"✅ Calibration complete! Now monitoring both neck and back...")
            
            # Active monitoring after calibration
            else:
                # Debug info
                print(f"📐 Neck: {neck_angle:.1f}° (>{self.neck_threshold}?) | Back: {back_angle:.1f}° (>{self.back_threshold}?)")
                
                # Check for NECK slouching
                neck_slouching = neck_angle > self.neck_threshold
                # Check for BACK slouching  
                back_slouching = back_angle > self.back_threshold
                
                # Combined slouch detection
                is_slouching = neck_slouching or back_slouching
                
                if is_slouching:
                    if self.slouch_start is None:
                        self.slouch_start = time.time()
                        # Determine which type of slouch
                        if neck_slouching and back_slouching:
                            slouch_type = "neck and back"
                        elif neck_slouching:
                            slouch_type = "neck"
                        else:
                            slouch_type = "back"
                        print(f"⚠️ {slouch_type.title()} slouch detected!")
                    
                    # Check if slouch has lasted long enough to trigger alert
                    elif time.time() - self.slouch_start >= self.slouch_duration:
                        if neck_slouching and back_slouching:
                            alert = f"Bad posture! Straighten your neck and back. (Neck: {neck_angle:.1f}°, Back: {back_angle:.1f}°)"
                        elif neck_slouching:
                            alert = f"Neck strain! Sit upright. (Neck angle: {neck_angle:.1f}°)"
                        else:
                            alert = f"Hunched back! Straighten your spine. (Back angle: {back_angle:.1f}°)"
                        print(f"🚨 POSTURE ALERT: {alert}")
                else:
                    # Reset if posture is corrected
                    if self.slouch_start is not None:
                        print(f"✅ Posture corrected")
                    self.slouch_start = None
        
        return neck_angle, back_angle, alert

    def close(self):
        self.pose.close()