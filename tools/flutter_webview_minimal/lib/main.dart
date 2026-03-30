import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'geolocation_service.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late final WebViewController _controller;
  late GeolocationService _geoService;
  
  final String initialUrl = 'http://192.168.5.144:5000';
  bool _geoInitialized = false;
  String _geoStatus = '📍 Initialisation...';

  @override
  void initState() {
    super.initState();
    _initializeWebView();
    _initializeGeolocation();
  }

  void _initializeWebView() {
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..addJavaScriptChannel('GeoLocation',
        onMessageReceived: (JavaScriptMessage message) {
          _handleJavaScriptMessage(message.message);
        },
      )
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (url) {
            debugPrint('📄 Page started: $url');
          },
          onPageFinished: (url) {
            debugPrint('📄 Page finished: $url');
            // Inject JavaScript interface
            _injectGeolocationInterface();
          },
          onNavigationRequest: (request) {
            return NavigationDecision.navigate;
          },
          onWebResourceError: (error) {
            debugPrint('❌ Web Error: ${error.description}');
          },
        ),
      )
      ..loadRequest(Uri.parse(initialUrl));
  }

  Future<void> _initializeGeolocation() async {
    try {
      _geoService = GeolocationService(
        apiBaseUrl: 'http://192.168.5.144:5000',
        authToken: 'token_placeholder', // Will be set from WebView
        onPositionUpdate: (position) {
          setState(() {
            _geoStatus = 
              '✅ (${position.latitude.toStringAsFixed(4)}, '
              '${position.longitude.toStringAsFixed(4)})';
          });
          // Send to WebView
          _controller.runJavaScript(
            "window.onGeoLocationUpdate && window.onGeoLocationUpdate("
            "${position.latitude}, ${position.longitude}, ${position.accuracy})"
          );
        },
        onError: (error) {
          setState(() {
            _geoStatus = '❌ $error';
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(error),
              backgroundColor: Colors.red,
              duration: const Duration(seconds: 3),
            ),
          );
        },
      );

      final initialized = await _geoService.initialize();
      if (initialized && mounted) {
        setState(() {
          _geoInitialized = true;
          _geoStatus = '✅ Prêt pour suivi';
        });
      }
    } catch (e) {
      setState(() {
        _geoStatus = '❌ Erreur: $e';
      });
    }
  }

  void _handleJavaScriptMessage(String message) {
    debugPrint('📨 JavaScript Message: $message');
    
    if (message.startsWith('START_TRACKING')) {
      _toggleTracking(true);
    } else if (message.startsWith('STOP_TRACKING')) {
      _toggleTracking(false);
    } else if (message.startsWith('SET_TOKEN:')) {
      final token = message.replaceFirst('SET_TOKEN:', '');
      _geoService.authToken = token;
      debugPrint('🔐 Token set from WebView');
    }
  }

  void _toggleTracking(bool start) {
    if (start) {
      _geoService.startTracking(intervalSeconds: 30);
      setState(() {
        _geoStatus = '🔴 Suivi ACTIF';
      });
    } else {
      _geoService.stopTracking();
      setState(() {
        _geoStatus = '⏹️ Suivi arrêté';
      });
    }
    
    // Notify WebView
    _controller.runJavaScript(
      "window.onTrackingStatusChanged && window.onTrackingStatusChanged('${start ? 'active' : 'stopped'}')"
    );
  }

  void _injectGeolocationInterface() {
    _controller.runJavaScript('''
      window.SofatelcomGeo = {
        startTracking: function() {
          GeoLocation.postMessage('START_TRACKING');
        },
        stopTracking: function() {
          GeoLocation.postMessage('STOP_TRACKING');
        },
        setAuthToken: function(token) {
          GeoLocation.postMessage('SET_TOKEN:' + token);
        },
        isTracking: function() {
          return document.querySelector('[data-tracking="true"]') !== null;
        }
      };
      console.log('✅ SofatelcomGeo interface injected');
    ''');
  }

  @override
  void dispose() {
    _geoService.stopTracking();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sofatelcom Mobile',
      theme: ThemeData(
        primarySwatch: Colors.red,
        useMaterial3: true,
      ),
      home: Scaffold(
        appBar: AppBar(
          title: const Text('Sofatelcom Mobile'),
          centerTitle: true,
          elevation: 0,
          actions: [
            // Geolocation Status Badge
            Padding(
              padding: const EdgeInsets.all(12.0),
              child: Center(
                child: GestureDetector(
                  onTap: _geoInitialized 
                    ? () => _toggleTracking(!_geoService.isTracking)
                    : null,
                  child: Tooltip(
                    message: _geoStatus,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: _geoService.isTracking 
                          ? Colors.red.shade600
                          : Colors.grey.shade600,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _geoService.isTracking 
                              ? Icons.location_on 
                              : Icons.location_off,
                            color: Colors.white,
                            size: 16,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            _geoService.isTracking ? 'ACTIF' : 'INACTIF',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
        body: SafeArea(
          child: WebViewWidget(controller: _controller),
        ),
        bottomSheet: !_geoInitialized
          ? Container(
              color: Colors.orange.shade50,
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _geoStatus,
                      style: TextStyle(color: Colors.orange.shade900),
                    ),
                  ),
                ],
              ),
            )
          : null,
      ),
    );
  }
}
