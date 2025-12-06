# blink_detector.py
import math
import mediapipe as mp
import numpy as np
from collections import deque
import time


mp_face_mesh = mp.solutions.face_mesh

# landmark indices for eyes in mediapipe face mesh
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def _euclid(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def eye_aspect_ratio(landmarks, eye_indices, image_w, image_h):
    # returns EAR for one eye
    pts = []
    for idx in eye_indices:
        lm = landmarks[idx]
        pts.append((lm.x * image_w, lm.y * image_h))
    # p1 p2 p3 p4 p5 p6 corresponds to indexes used in EAR formula
    p1, p2, p3, p4, p5, p6 = pts
    vertical1 = _euclid(p2, p6)
    vertical2 = _euclid(p3, p5)
    horizontal = _euclid(p1, p4)
    # if horizontal distance is zero (or extremely small) landmarks are invalid
    if horizontal == 0 or horizontal < 1e-6:
        return None
    ear = (vertical1 + vertical2) / (2.0 * horizontal)
    return ear

def get_face_orientation(landmarks):
    """Calculate face orientation from face mesh landmarks."""
    # Use nose tip and points around face to determine orientation
    nose_tip = landmarks[1]  # Nose tip landmark
    left_face = landmarks[234]  # Left face edge
    right_face = landmarks[454]  # Right face edge
    
    # Calculate face direction based on nose position relative to face edges
    face_center_x = (left_face.x + right_face.x) / 2
    looking_direction = nose_tip.x - face_center_x
    
    # Calculate if person is looking down based on nose and chin positions
    chin = landmarks[152]  # Chin landmark
    looking_down = nose_tip.y > (chin.y * 0.95)  # Threshold for looking down
    
    return looking_direction, looking_down

class BlinkDetector:
    def __init__(self, ear_threshold=0.24, consec_frames=3):
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        self.counter = 0
        self.total_blinks = 0
        self.last_blink_time = None
        self.closed_start = None
        self.alert_active = False
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        # rolling queue of timestamps for last minute
        self.blink_times = deque()
        
        # For EAR smoothing
        self.ear_history = deque(maxlen=5)  # Keep last 5 EAR values
        self.looking_down_history = deque([False] * 3, maxlen=3)  # Keep last 3 looking down states
        
        # Thresholds
        self.looking_threshold = 0.15  # Threshold for significant head turn

    def process(self, image_rgb, image_w, image_h):
        results = self.face_mesh.process(image_rgb)
        ear = None
        alert = None
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # Get face orientation
            looking_direction, looking_down = get_face_orientation(landmarks)
            self.looking_down_history.append(looking_down)
            
            # Only process EAR when face is reasonably forward-facing
            if abs(looking_direction) < self.looking_threshold:
                left_ear = eye_aspect_ratio(landmarks, LEFT_EYE, image_w, image_h)
                right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, image_w, image_h)
                
                if left_ear is not None and right_ear is not None:
                    ear = (left_ear + right_ear) / 2.0
                    self.ear_history.append(ear)
                    
                    # Use smoothed EAR for more stable detection
                    smoothed_ear = np.mean(self.ear_history) if self.ear_history else ear
                    
                    if smoothed_ear < self.ear_threshold:
                        self.counter += 1
                        if self.closed_start is None:
                            self.closed_start = time.time()
                    else:
                        if self.counter >= self.consec_frames:
                            self.total_blinks += 1
                            ts = time.time()
                            self.blink_times.append(ts)
                            # drop blinks older than 60 seconds
                            while self.blink_times and (ts - self.blink_times[0] > 60):
                                self.blink_times.popleft()
                        self.counter = 0
                        self.closed_start = None
                        
            else:
                # Reset counters when face is turned significantly
                self.counter = 0
                self.closed_start = None
                self.alert_active = False

            # Drowsiness detection with improved checks
            if self.closed_start:
                closed_duration = time.time() - self.closed_start
                # Check if consistently looking down
                consistently_down = all(self.looking_down_history)
                
                # Alert only if eyes closed for long AND not consistently looking down
                if closed_duration > 4.0 and not consistently_down:
                    if not self.alert_active:
                        alert = f"Eyes closed for {closed_duration:.1f}s — possible drowsiness"
                        self.alert_active = True
                elif closed_duration <= 2.0 or consistently_down:
                    self.alert_active = False

        # always return a 4-tuple so callers can safely unpack
        return ear, self.total_blinks, len(self.blink_times), alert

    def close(self):
        self.face_mesh.close()
