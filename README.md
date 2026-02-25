# SMART HEALTH MONITORING SYSTEM
An real time digital wellness system that monitors eye blinks, posture and screen time behaviour using computer vision and IoT principles to promote healthier digital habits.

## Problem Statement
Prolonged screen exposure leads to:
- Eye strain
- Poor posture
- Fatigue
- Reduced productivity
Most solutions are either expensive wearables or simple reminder apps.
This project provides an integrated, low-cost, real-time monitoring system using a webcam and AI-based detection.

## System Architecture
The system follows a modular, real-time architecture:
- Data Acquisition Layer
  - Webcam video capture (30 FPS)
  - Frame preprocessing
- Processing Layer
  - Blink Detection (MediaPipe Face Mesh + EAR calculation)
  - Posture Detection (MediaPipe Pose)
  - Alert Management System
- Storage & Reporting Layer
  - Local CSV logging
  - Firebase Realtime Database sync
  - Health Report Generator

## Tech Stack
  - Language
    - Python 3.10+
  - Computer Vision & AI
    - OpenCV
    - MediaPipe
    - TensorFlow Lite
  - Data Handling
    - Pandas
    - CSV logging
    - Firebase Realtime Database
  - UI & Notifications
    - Tkinter / CustomTkinter
    - Plyer / Win10Toast

## Key Features
  - Real-time blink detection using Eye Aspect Ratio (EAR)
  - Posture angle monitoring with slouch detection
  - Instant alerts for drowsiness and bad posture
  - Health dashboard with screen-time insights
  - Cloud synchronization (Firebase)
  - Automated report generation
  - Privacy-focused local data processing
 
## Core Detection Logic
- Blink Detection
  - Uses MediaPipe Face Mesh
  - Computes Eye Aspect Ratio (EAR)
  - Triggers alert if eyes closed > 2 seconds
- Posture Detection
  - Tracks neck and torso landmarks
  - Calculates neck angle
  - Triggers alert if angle > 25° for > 2 seconds

## File Structure
```bash
├── main.py
├── blink_detector.py
├── posture_detector.py
├── data_logger.py
├── firebase_logger.py
├── health_report.py
├── ui_notifications.py
└── requirements.txt
```

## Installation
```bash
git clone <repo-link>
cd smart-health-monitor
pip install -r requirements.txt
python main.py
```

## Future Improvements
- AI-based predictive fatigue scoring
- Mobile companion app
- Telemedicine integration
- Enhanced posture calibration
- Multi-sensor integration (ECG, SpO₂)
