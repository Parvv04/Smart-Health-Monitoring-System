# Firebase Setup Instructions

1. **Go to Firebase Console**: https://console.firebase.google.com/

2. **Create a New Project**:
   - Project name: `smart-health-monitor`
   - Disable Google Analytics (not needed)

3. **Enable Realtime Database**:
   - Go to Build > Realtime Database
   - Create database in `asia-southeast1` region
   - Start in test mode (rules will be public temporarily)

4. **Get Service Account Key**:
   - Go to Project Settings > Service Accounts
   - Click "Generate New Private Key"
   - Save as `firebase_config.json` in your project folder

5. **Database Rules** (for production):
```json
{
  "rules": {
    "health_logs": {
      ".read": "auth != null",
      ".write": "auth != null"
    }
  }
}