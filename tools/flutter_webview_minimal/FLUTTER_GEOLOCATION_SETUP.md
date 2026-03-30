# 📱 SOFATELCOM Mobile - Flutter Geolocation Integration

## 📋 Overview

This Flutter application integrates real-time GPS tracking with the SOFATELCOM web dashboard via WebView. The `GeolocationService` runs in the background and sends location updates to the backend API.

## ✨ Features

✅ **Real-time GPS Tracking** - Updates sent every 30 seconds  
✅ **Permission Management** - Automatic Android/iOS permission requests  
✅ **Rate Limiting** - Prevents excessive API calls (30s minimum interval)  
✅ **Background Tracking** - Continues tracking in background mode  
✅ **WebView Integration** - Bridges native GPS with web dashboard  
✅ **Error Handling** - Graceful fallback on permission denial  
✅ **Token Management** - Dynamic auth token refresh support  

## 🚀 Quick Start

### Prerequisites
- Flutter 3.0.0+ (SDK >=3.0.0 <4.0.0)
- Android 5.0+ (API 21) or iOS 12.0+
- Active internet connection to SOFATELCOM backend (http://192.168.1.12:5000)

### Installation

1. **Install dependencies:**
```bash
cd tools/flutter_webview_minimal
flutter pub get
```

2. **Update Android configuration** (required):
   - Ensure `android/app/src/main/AndroidManifest.xml` has GPS permissions:
   ```xml
   <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
   <uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />
   ```

3. **Update iOS configuration** (required):
   - Ensure `ios/Runner/Info.plist` has location descriptions:
   ```xml
   <key>NSLocationWhenInUseUsageDescription</key>
   <string>SOFATELCOM a besoin d'accéder à votre localisation...</string>
   <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
   <string>SOFATELCOM a besoin d'accéder à votre localisation à tout moment...</string>
   ```

4. **Configure Backend URL** (in `lib/main.dart`):
   ```dart
   final String initialUrl = 'http://192.168.1.12:5000';
   ```
   Change `192.168.1.12` to your actual backend IP/hostname.

5. **Build and run:**
   ```bash
   flutter run
   ```

## 🔧 Architecture

```
main.dart
  ├── WebViewController (loads http://192.168.1.12:5000)
  ├── GeolocationService
  │   ├── Permission handling (geolocator)
  │   ├── Position tracking (Timer every 30s)
  │   ├── API POST to /api/tracking
  │   └── Callbacks (onPositionUpdate, onError)
  └── JavaScript Bridge (GeoLocation channel)
       ├── START_TRACKING message
       ├── STOP_TRACKING message
       └── SET_TOKEN:xyz message

Dashboard (Web)
  ├── dashboard_chef_pur.html
  ├── mobile-geolocation-integration.js (MobileGeo)
  └── map-realtime.js (MapTracker - receives updates)
```

## 📡 API Integration

### Location Update Endpoint
**POST** `/api/tracking`

**Request:**
```json
{
  "latitude": 36.7372,
  "longitude": 3.0588,
  "accuracy": 5.2,
  "speed": 15.5,
  "altitude": 120,
  "timestamp": "2026-01-15T10:30:00Z",
  "status": "en_route"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "tracking_id": 12345,
  "distance_traveled": 2.5,
  "intervention_id": 789,
  "timestamp": "2026-01-15T10:30:00Z"
}
```

**Rate Limiting:**
- Maximum 1 update per 30 seconds per technician
- Returns HTTP 429 if exceeded, with `retry_after` header

### Authentication
- Token passed via JavaScript: `MobileGeo.init()` extracts from localStorage
- Bearer token in header: `Authorization: Bearer <token>`
- Token can be refreshed via `/api/mobile/refresh` endpoint

## 🎯 Usage

### In the Flutter App
The tracking automatically activates when the user logs in. The status badge in the app bar shows:
- 🟢 **INACTIF** (inactive, click to start)
- 🔴 **ACTIF** (actively tracking)

### In the Web Dashboard
Once logged into `http://192.168.1.12:5000`, the dashboard receives live location updates:

```html
<!-- Add these buttons to your dashboard -->
<button data-action="start-tracking">📍 Démarrer suivi</button>
<button data-action="stop-tracking">⏹️ Arrêter suivi</button>
<button data-action="toggle-tracking">🔄 Basculer suivi</button>

<!-- Status display -->
<span data-tracking-badge>⏹️ INACTIF</span>
<span data-tracking-status>Localisation...</span>
```

Then in your JavaScript:
```javascript
// Start tracking
MobileGeo.startTracking();

// Stop tracking
MobileGeo.stopTracking();

// Get status
console.log(MobileGeo.getStatus());
```

## ⚙️ Configuration

### Tracking Interval
In `lib/geolocation_service.dart`:
```dart
_geoService.startTracking(intervalSeconds: 30);  // Change 30 to desired interval
```

### GPS Accuracy Threshold
In `lib/geolocation_service.dart`:
```dart
desiredAccuracy: LocationAccuracy.best,  // Options: worst, low, medium, high, best, bestForNavigation
```

### Backend URL
In `lib/main.dart`:
```dart
final String initialUrl = 'http://192.168.1.12:5000';
_geoService = GeolocationService(
  apiBaseUrl: 'http://192.168.1.12:5000',
```

## 🔐 Permissions

### Android Permissions Required
- ✅ `ACCESS_FINE_LOCATION` - Precise GPS location
- ✅ `ACCESS_COARSE_LOCATION` - Approximate location (network-based)
- ✅ `ACCESS_BACKGROUND_LOCATION` - Background tracking
- ✅ `INTERNET` - API calls
- ✅ `WAKE_LOCK` - Keep device awake during tracking

Declared in `android/app/src/main/AndroidManifest.xml`

### iOS Permissions Required
- ✅ `NSLocationWhenInUseUsageDescription` - Location while using app
- ✅ `NSLocationAlwaysAndWhenInUseUsageDescription` - Background location
- ⚠️ Enable `Background Modes > Location` in Xcode (UIBackgroundModes)

Declared in `ios/Runner/Info.plist`

### Runtime Permission Flow
1. App requests permission from `permission_handler` plugin
2. User grants/denies in dialog
3. If denied, error callback shows message to user
4. If permanently denied, app opens Settings page

## 🐛 Troubleshooting

### "Location permission denied"
- **Android**: Settings → Apps → SOFATELCOM → Permissions → Location → Allow
- **iOS**: Settings → SOFATELCOM → Location → Always

### "Tracking not working on map"
1. Ensure `mobile-geolocation-integration.js` is included in HTML
2. Check browser console for errors (F12)
3. Verify auth token is set: `console.log(localStorage.getItem('access_token'))`
4. Test API endpoint: `curl -H "Authorization: Bearer TOKEN" http://192.168.1.12:5000/api/tracking`

### "Position not updating"
1. Check that interval is correct (default 30s)
2. Verify GPS is enabled on device
3. Check signal strength (may take longer to get position)
4. Look for rate limiting errors (HTTP 429)

### "WebView not loading"
1. Check URL: `192.168.1.12:5000`
2. Verify backend is running: `curl http://192.168.1.12:5000`
3. Check Android network security config (allows HTTP in dev)
4. For iOS, check ATS (App Transport Security) exceptions

## 📊 Testing

### Test Endpoints
```bash
# Login to get token
curl -X POST http://192.168.1.12:5000/api/mobile/login \
  -H "Content-Type: application/json" \
  -d '{"username":"technicien1","password":"password"}'

# Send test position
curl -X POST http://192.168.1.12:5000/api/tracking \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 36.7372,
    "longitude": 3.0588,
    "accuracy": 10.5,
    "speed": 20.0,
    "status": "en_route"
  }'

# Check SSE stream
curl -N http://192.168.1.12:5000/api/stream/gps
```

### Local Testing
```bash
# Run on Android emulator
flutter run

# Run on iOS simulator
flutter run -d iOS

# Run on real device
flutter run -d <device-id>
```

## 📚 Related Files

- **Flutter App**: `tools/flutter_webview_minimal/lib/main.dart`
- **Geolocation Service**: `tools/flutter_webview_minimal/lib/geolocation_service.dart`
- **Mobile Integration**: `static/js/mobile-geolocation-integration.js`
- **Real-time Map**: `static/js/map-realtime.js`
- **Backend API**: `routes/mobile.py` (/api/tracking endpoint)
- **GPS Stream API**: `routes/gps_stream.py` (/api/stream/gps endpoint)
- **Backend Utilities**: `utils_tracking.py` (validation & rate limiting)

## 🚀 Deployment

### Android
```bash
cd android
./gradlew clean
./gradlew bundle  # For Play Store
./gradlew assembleRelease  # For APK
```

### iOS
```bash
cd ios
pod install
open Runner.xcworkspace
# Build in Xcode
```

## 📝 License

This mobile app is part of SOFATELCOM and follows the same license terms as the main project.
