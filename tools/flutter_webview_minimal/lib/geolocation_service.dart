import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

/// 📍 MOBILE GEOLOCATION SERVICE
/// Handles GPS tracking and location updates for Flutter WebView app

class GeolocationService {
  static const String TAG = '[GEOLOCATION]';
  
  final String apiBaseUrl;
  String authToken;  // Made mutable for runtime token updates
  final Function(Position) onPositionUpdate;
  final Function(String) onError;
  
  Timer? _trackingTimer;
  Position? _lastPosition;
  bool _isTracking = false;
  int _updateIntervalSeconds = 30;
  
  GeolocationService({
    required this.apiBaseUrl,
    required this.authToken,
    required this.onPositionUpdate,
    required this.onError,
  });
  
  /// Initialize geolocation and request permissions
  Future<bool> initialize() async {
    print('$TAG Initializing geolocation service...');
    
    try {
      // Check location permission
      final status = await Permission.location.request();
      
      if (status.isGranted) {
        print('$TAG Location permission granted');
        return true;
      } else if (status.isDenied) {
        onError('Permission de géolocalisation refusée');
        return false;
      } else if (status.isPermanentlyDenied) {
        onError('Permission de géolocalisation désactivée. Vérifiez les paramètres.');
        openAppSettings();
        return false;
      }
      
      return false;
    } catch (e) {
      onError('Erreur initialisation géolocalisation: $e');
      return false;
    }
  }
  
  /// Start background location tracking
  Future<void> startTracking({int intervalSeconds = 30}) async {
    print('$TAG Starting location tracking (${intervalSeconds}s interval)...');
    
    if (_isTracking) {
      print('$TAG Tracking already active');
      return;
    }
    
    _updateIntervalSeconds = intervalSeconds;
    _isTracking = true;
    
    // Get first position immediately
    try {
      final locationSettings = LocationSettings(
        accuracy: LocationAccuracy.best,
        distanceFilter: 0,
      );
      
      final position = await Geolocator.getCurrentPosition(
        locationSettings: locationSettings,
      );
      await _sendPositionUpdate(position);
    } catch (e) {
      onError('Erreur obtenir position: $e');
    }
    
    // Set up periodic updates
    _trackingTimer = Timer.periodic(
      Duration(seconds: _updateIntervalSeconds),
      (_) async {
        try {
          final locationSettings = LocationSettings(
            accuracy: LocationAccuracy.best,
            distanceFilter: 0,
          );
          
          final position = await Geolocator.getCurrentPosition(
            locationSettings: locationSettings,
          );
          await _sendPositionUpdate(position);
        } catch (e) {
          print('$TAG Error getting position: $e');
        }
      },
    );
  }
  
  /// Stop location tracking
  void stopTracking() {
    print('$TAG Stopping location tracking');
    _isTracking = false;
    _trackingTimer?.cancel();
    _trackingTimer = null;
  }
  
  /// Get current position once
  Future<Position?> getCurrentPosition() async {
    try {
      final locationSettings = LocationSettings(
        accuracy: LocationAccuracy.best,
        distanceFilter: 0,
      );
      
      return await Geolocator.getCurrentPosition(
        locationSettings: locationSettings,
      );
    } catch (e) {
      onError('Erreur position: $e');
      return null;
    }
  }
  
  /// Send position to backend
  Future<void> _sendPositionUpdate(Position position) async {
    try {
      // Check if position changed significantly (more than 10m)
      if (_lastPosition != null) {
        final distance = Geolocator.distanceBetween(
          _lastPosition!.latitude,
          _lastPosition!.longitude,
          position.latitude,
          position.longitude,
        );
        
        if (distance < 10) {
          print('$TAG Position unchanged (<10m), skipping update');
          return;
        }
      }
      
      _lastPosition = position;
      
      // Call callback
      onPositionUpdate(position);
      
      // Send to backend
      await _postTracking(position);
      
      print('$TAG Position updated: (${position.latitude.toStringAsFixed(4)}, ${position.longitude.toStringAsFixed(4)})');
      
    } catch (e) {
      print('$TAG Error sending position: $e');
    }
  }
  
  /// POST tracking data to server
  Future<void> _postTracking(Position position) async {
    try {
      final url = Uri.parse('$apiBaseUrl/api/tracking');
      
      final response = await http.post(
        url,
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'latitude': position.latitude,
          'longitude': position.longitude,
          'accuracy': position.accuracy,
          'altitude': position.altitude,
          'speed': position.speed,
          'speed_accuracy': position.speedAccuracy,
          'timestamp': DateTime.now().toUtc().toIso8601String(),
          'status': _getCurrentStatus(),
        }),
      );
      
      if (response.statusCode == 201 || response.statusCode == 200) {
        print('$TAG Position sent successfully');
      } else if (response.statusCode == 429) {
        print('$TAG Rate limited, will retry later');
      } else {
        print('$TAG Server error: ${response.statusCode}');
      }
      
    } catch (e) {
      print('$TAG Error posting tracking: $e');
    }
  }
  
  /// Get current status (can be overridden by UI)
  String _getCurrentStatus() {
    // Determine status based on speed
    if (_lastPosition != null && _lastPosition!.speed > 5) {
      return 'en_route';
    }
    return 'on_site';
  }
  
  /// Check if tracking is active
  bool get isTracking => _isTracking;
  
  /// Get last known position
  Position? get lastPosition => _lastPosition;
}


/// 📍 FLUTTER WEBVIEW APP WITH GEOLOCATION
class GeolocationWebViewApp extends StatefulWidget {
  const GeolocationWebViewApp({Key? key}) : super(key: key);
  
  @override
  State<GeolocationWebViewApp> createState() => _GeolocationWebViewAppState();
}

class _GeolocationWebViewAppState extends State<GeolocationWebViewApp> {
  late GeolocationService _geoService;
  bool _locationEnabled = false;
  String _statusMessage = 'Initialisation...';
  Position? _currentPosition;
  
  @override
  void initState() {
    super.initState();
    _initializeGeolocation();
  }
  
  Future<void> _initializeGeolocation() async {
    // Initialize geolocation service
    _geoService = GeolocationService(
      apiBaseUrl: 'http://192.168.1.12:5000',
      authToken: _getAuthToken(),  // Get from shared preferences
      onPositionUpdate: (position) {
        setState(() {
          _currentPosition = position;
          _statusMessage = 'Position: ${position.latitude.toStringAsFixed(4)}, ${position.longitude.toStringAsFixed(4)}';
        });
      },
      onError: (error) {
        setState(() {
          _statusMessage = error;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error)),
        );
      },
    );
    
    // Request permissions
    final initialized = await _geoService.initialize();
    
    if (initialized && mounted) {
      setState(() {
        _statusMessage = 'Prêt pour suivi';
      });
    }
  }
  
  void _toggleTracking() {
    if (_geoService.isTracking) {
      _geoService.stopTracking();
      setState(() {
        _locationEnabled = false;
        _statusMessage = 'Suivi arrêté';
      });
    } else {
      _geoService.startTracking(intervalSeconds: 30);
      setState(() {
        _locationEnabled = true;
        _statusMessage = 'Suivi actif...';
      });
    }
  }
  
  String _getAuthToken() {
    // Retrieve auth token from SharedPreferences or secure storage
    // For now, return placeholder
    return 'your_auth_token_here';
  }
  
  @override
  void dispose() {
    _geoService.stopTracking();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SOFATELCOM - Mobile'),
        actions: [
          // Location tracking button
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Center(
              child: GestureDetector(
                onTap: _toggleTracking,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _locationEnabled ? Icons.location_on : Icons.location_off,
                      color: _locationEnabled ? Colors.green : Colors.grey,
                    ),
                    Text(
                      _locationEnabled ? 'Actif' : 'Inactif',
                      style: TextStyle(
                        fontSize: 10,
                        color: _locationEnabled ? Colors.green : Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Status bar
          Container(
            color: _locationEnabled ? Colors.green.shade50 : Colors.grey.shade100,
            padding: const EdgeInsets.all(12.0),
            child: Row(
              children: [
                Icon(
                  _locationEnabled ? Icons.check_circle : Icons.info,
                  color: _locationEnabled ? Colors.green : Colors.orange,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Suivi de localisation',
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      Text(
                        _statusMessage,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          // Location details
          if (_currentPosition != null)
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Coordonnées GPS:', style: Theme.of(context).textTheme.titleSmall),
                      Text('Lat: ${_currentPosition!.latitude.toStringAsFixed(6)}'),
                      Text('Lon: ${_currentPosition!.longitude.toStringAsFixed(6)}'),
                      Text('Accuracy: ${_currentPosition!.accuracy.toStringAsFixed(1)}m'),
                      Text('Altitude: ${_currentPosition!.altitude.toStringAsFixed(1)}m'),
                      Text('Speed: ${(_currentPosition!.speed * 3.6).toStringAsFixed(1)} km/h'),
                    ],
                  ),
                ),
              ),
            ),
          // Tracking toggle button
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: ElevatedButton.icon(
              onPressed: _toggleTracking,
              icon: Icon(_locationEnabled ? Icons.stop : Icons.play_arrow),
              label: Text(_locationEnabled ? 'Arrêter le suivi' : 'Démarrer le suivi'),
              style: ElevatedButton.styleFrom(
                backgroundColor: _locationEnabled ? Colors.red : Colors.green,
                minimumSize: const Size(double.infinity, 50),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

void main() {
  runApp(
    MaterialApp(
      title: 'SOFATELCOM Mobile',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const GeolocationWebViewApp(),
    ),
  );
}