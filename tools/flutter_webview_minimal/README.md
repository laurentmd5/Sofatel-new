Sofatelcom WebView minimal

Purpose
- Minimal Flutter wrapper that loads the existing Sofatelcom web UI inside a WebView.
- No manual token handling: the web pages' own session login is used.

Quickstart
1. Install Flutter and Android/iOS toolchains.
2. Open project: `cd tools/flutter_webview_minimal`.
3. Run on Android emulator with local dev server: `flutter run` (set `initialUrl` in `lib/main.dart` to `http://10.0.2.2:5000/`).
4. To test on a real device, set `initialUrl` to your machine's LAN IP or a public URL and run `flutter run`.

Permissions & notes
- Android (add to `android/app/src/main/AndroidManifest.xml`):
  <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
  <uses-permission android:name="android.permission.CAMERA" />
  <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
  <!-- Android 13+ uses READ_MEDIA_IMAGES instead of READ_EXTERNAL_STORAGE -->

  Notes: WebView on Android may require a custom WebChromeClient to grant geolocation and file chooser access — many plugins handle this but be prepared to implement a small native bridge if file input doesn't open camera/gallery.

- iOS (add to `ios/Runner/Info.plist`):
  <key>NSLocationWhenInUseUsageDescription</key>
  <string>Nous utilisons la géolocalisation pour remplir automatiquement la position des interventions.</string>
  <key>NSCameraUsageDescription</key>
  <string>Besoin d'accéder à la caméra pour prendre des photos justificatives.</string>
  <key>NSPhotoLibraryUsageDescription</key>
  <string>Accès à la galerie pour sélectionner des photos justificatives.</string>

Testing checklist
- Test the site in mobile browser first (responsive CSS) and verify geolocation and file input.
- Then run the Flutter app and verify the same flows inside the WebView.

Limitations
- This minimal app doesn't implement advanced file chooser handling or background tracking.
- If file inputs don't work on some devices, a small native handling will be required.
