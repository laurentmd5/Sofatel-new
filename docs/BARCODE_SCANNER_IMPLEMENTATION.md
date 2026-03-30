# Barcode Scanner Implementation - Sprint 2, Task 2.2

## Overview

The Mobile Barcode Scanner is a mobile-optimized feature that enables SOFATELCOM technicians and staff to quickly scan products, interventions, and demands using their mobile devices. The feature includes:

- **Live camera feed** with barcode detection (supports multiple formats)
- **Manual entry fallback** when camera is unavailable
- **Product scanning** with stock information and reservation capability
- **Intervention tracking** by barcode
- **Demand (ND) lookup** for intervention requests
- **Scan history** with logging and analytics
- **Mobile-first responsive design** (iOS/Android compatible)
- **JWT-protected API** endpoints with permission checks

## Architecture

### Frontend (HTML + JavaScript)

**File**: `templates/barcode_scanner.html`

- **Quagga2 library** for barcode detection (supports: Code128, EAN, UPC, Codabar)
- **Camera stream** via WebRTC (fallback to manual input)
- **Responsive UI** with Material Design principles
- **Debounce mechanism** to prevent duplicate scans (1-second window)
- **Real-time visual feedback** (scan guide, loading states, results)

### Backend (Flask + SQLAlchemy)

**File**: `routes/mobile.py` - Barcode Scanner API Endpoints

#### Core Endpoints

```
POST /api/barcode/scan
POST /api/barcode/manual
GET  /api/barcode/history
POST /api/barcode/log-scan
GET  /scanner  (HTML page)
```

#### Product Scanning

**Request**:
```json
{
  "barcode": "BARCODE_TEST_001",
  "type": "product",
  "action": "lookup"
}
```

**Response** (Success):
```json
{
  "success": true,
  "type": "product",
  "data": {
    "id": 42,
    "nom": "Test Product",
    "code_produit": "BARCODE_TEST_001",
    "quantite_stock": 100,
    "prix_unitaire": 150.00,
    "stock_min": 10,
    "sla_status": "ok"
  }
}
```

#### Product Reservation

**Request**:
```json
{
  "barcode": "BARCODE_TEST_001",
  "type": "product",
  "action": "reserve"
}
```

**Response**:
```json
{
  "success": true,
  "type": "product",
  "data": {
    "id": 42,
    "nom": "Test Product",
    "reservation_status": "created",
    "reservation_id": 123
  }
}
```

#### Intervention Scanning

**Request**:
```json
{
  "barcode": "INT_001",
  "type": "intervention"
}
```

**Response**:
```json
{
  "success": true,
  "type": "intervention",
  "data": {
    "intervention_id": 1,
    "statut": "en_cours",
    "date_debut": "2024-01-15T09:30:00",
    "demande": {
      "nd": "TEST_ND_001",
      "nom_client": "Client ABC",
      "zone": "ZONE_A",
      "type_techno": "Fibre"
    }
  }
}
```

#### Demand (ND) Scanning

**Request**:
```json
{
  "barcode": "TEST_ND_001",
  "type": "nd"
}
```

**Response**:
```json
{
  "success": true,
  "type": "nd",
  "data": {
    "nd": "TEST_ND_001",
    "nom_client": "Client ABC",
    "zone": "ZONE_A",
    "priorite_traitement": "NORMALE",
    "statut": "nouveau",
    "intervention_id": 1,
    "intervention_statut": "en_cours"
  }
}
```

#### Scan History

**Request**:
```
GET /api/barcode/history?page=1&per_page=20&type=product
```

**Response**:
```json
{
  "success": true,
  "page": 1,
  "per_page": 20,
  "total": 45,
  "total_pages": 3,
  "history": [
    {
      "id": 1,
      "timestamp": "2024-01-15T10:30:45.123456",
      "barcode": "BARCODE_TEST_001",
      "type": "product",
      "action": "lookup",
      "result": "success"
    }
  ]
}
```

### Duplicate Prevention & Safeguards

1. **Scan Debounce**: Frontend prevents duplicate scans within 1 second (configurable)
2. **Barcode Validation**: Minimum 3 characters required
3. **Permission Checks**: Technicians can only access assigned interventions
4. **Activity Logging**: All scans are logged with timestamp, user, and result
5. **Stock Alerts**: Low-stock products flagged with visual indicator

## Security

### Authentication

- **JWT Bearer Tokens** required for all endpoints
- Tokens expire after 60 minutes (configurable: `ACCESS_TOKEN_EXPIRES_MINUTES`)
- Refresh tokens valid for 7 days
- Token stored in browser localStorage on mobile device

### Authorization

- **Technician Role**: Can only view/scan their own assigned interventions
- **Manager Roles**: Can view all interventions and products
- **Public Products**: Available to all authenticated users
- **Scope Enforcement**: Technician context automatically filters by user ID

### Data Protection

- HTTPS recommended in production
- Sensitive data (prices, client info) included in responses based on user role
- Scan logs stored with user ID and IP address for audit trail
- No barcode data persisted beyond activity logs

## Frontend Usage

### Page Access

```
GET /scanner
```

Accessible only to authenticated users (redirects to login if needed).

### JavaScript API

```javascript
// Start camera
startCamera();

// Perform scan
performScan(barcode);

// Scan from manual input
scanFromInput();

// Clear results
clearResults();

// Toggle camera on/off
toggleCamera();

// Set scan type (product|intervention|nd)
setScanType('product');

// Reserve product
reserveProduct(productId, productName);

// Log scan to backend
logScan(barcode, type, result, details);
```

### Error Handling

- **Camera not available**: Falls back to manual input with user notification
- **Invalid barcode**: Shows error message and maintains input focus
- **Network error**: Displays error with retry option
- **Unauthorized**: Redirects to login
- **Not found**: Shows 404 message with suggestions

### User Experience States

1. **Ready**: Camera active, scan guide visible, input focused
2. **Scanning**: Visual feedback (loading spinner)
3. **Success**: Result card displayed with product/intervention details
4. **Error**: Error message with red background
5. **Manual entry**: Input field focused, ready for keyboard input

## Database Integration

### Models Used

- `Produit`: Product catalog with `code_produit` (barcode) field
- `DemandeIntervention`: Demands with `nd` (unique identifier) field
- `Intervention`: Intervention records linked to demands
- `Reservation`: Product reservations with quantity tracking
- `ActivityLog`: Audit trail for all scan events
- `User`: Technician/staff with role-based permissions

### Activity Log Structure

```python
ActivityLog(
    user_id=user.id,
    action='barcode_scan',
    module='barcode_scanner',
    details={
        'barcode': '123456',
        'type': 'product',
        'action': 'lookup',
        'result': 'success',
        'extra': {...}
    },
    ip_address=request.remote_addr
)
```

## Supported Barcode Formats

- **Code 128** (alphanumeric, variable length)
- **EAN-13** (13 digits)
- **EAN-8** (8 digits)
- **UPC-A** (12 digits)
- **UPC-E** (compressed UPC)
- **Codabar** (variable length)

Additional formats can be enabled in Quagga2 configuration.

## Configuration

### Environment Variables

```bash
# Mobile API token expiry (minutes)
ACCESS_TOKEN_EXPIRES_MINUTES=60

# Refresh token expiry (days)
REFRESH_TOKEN_EXPIRES_DAYS=7

# Frontend cache TTL (seconds)
MOBILE_CACHE_TTL=10

# Daily import schedule
IMPORT_SCHEDULE_HOUR=6
IMPORT_SCHEDULE_MINUTE=0
IMPORT_FILE_PATH=/uploads/daily_import.xlsx
IMPORT_SERVICE=SAV
```

### Frontend Configuration

Edit `templates/barcode_scanner.html` constants:

```javascript
const SCAN_DEBOUNCE_MS = 1000;  // Prevent duplicate scans
const API_TOKEN = localStorage.getItem('mobile_access_token');
```

## Testing

### Test Coverage

**File**: `tests/test_barcode_scanner.py`

- **Product Scanning**: 4 tests (by barcode, by ID, not found, low stock)
- **Intervention Scanning**: 2 tests (by ID, by ND, authorization)
- **Demand Scanning**: 2 tests (by ND, not found)
- **Reservations**: 2 tests (create new, increment existing)
- **Manual Entry**: 1 test
- **Invalid Input**: 3 tests (empty, short, invalid type)
- **History**: 2 tests (retrieval, pagination)
- **Permissions**: 3 tests (no token, invalid token, expired token)
- **Logging**: 2 tests (basic logging, with details)
- **Integration**: 1 test (full workflow)

### Running Tests

```bash
# Run all barcode scanner tests
pytest tests/test_barcode_scanner.py -v

# Run specific test class
pytest tests/test_barcode_scanner.py::TestBarcodeProductScan -v

# Run with coverage
pytest tests/test_barcode_scanner.py --cov=routes.mobile --cov-report=html
```

## Integration with Existing Features

### Intervention Workflow

1. Technician scans intervention barcode at job site
2. System shows intervention details and linked demand
3. Technician can mark intervention complete via separate form
4. Scan logged to activity trail for audit purposes

### Product Reservation

1. Technician scans product barcode
2. System displays stock level and pricing
3. Technician clicks "Réserver" to create/update reservation
4. Reservation queued for approval by inventory manager

### Quality Assurance

- All scans logged for compliance and auditing
- Scan history available per user/date for metrics
- Stock tracking improvements via barcode-based movements

## Mobile Optimization

### Browser Compatibility

- ✅ Chrome/Chromium (Android)
- ✅ Firefox (Android)
- ✅ Safari (iOS)
- ✅ Edge (mobile)
- ⚠️ IE 11 (manual entry only, no camera)

### Performance

- Debounced scans reduce server load
- Frontend caching of results (5-second TTL)
- Efficient image processing via Quagga2
- Minimal network requests for each scan

### Accessibility

- Large touch targets (48px minimum)
- High contrast UI (WCAG AA compliant)
- Keyboard input support (Enter to scan)
- Screen reader friendly (alt text, ARIA labels)

## Troubleshooting

### Camera Not Starting

**Solution**: Check browser permissions and HTTPS requirement:
```javascript
// Debug: Check browser console
console.log('[CAMERA] Init failed:', err);
```

### Barcodes Not Detected

1. **Adjust camera angle**: Hold device perpendicular to barcode
2. **Improve lighting**: Ensure adequate brightness
3. **Clean lens**: Dust can affect detection
4. **Try manual entry**: Input barcode directly

### Scan Results Incorrect

1. Verify barcode format matches product field
2. Check product `code_produit` in database
3. Review activity logs for scan history
4. Test with different barcode

### Permission Denied

1. User not authenticated: Re-login required
2. User role insufficient: Contact admin
3. Technician accessing wrong intervention: Verify assignment

## Future Enhancements

- [ ] Batch scanning (multiple items per scan session)
- [ ] Voice input fallback
- [ ] QR code support (in addition to barcodes)
- [ ] Offline scanning with sync on reconnect
- [ ] Real-time stock updates via WebSocket
- [ ] Barcode generation for interventions
- [ ] Analytics dashboard (most scanned products, peak times)
- [ ] Multi-location inventory support
- [ ] Barcode label printing from web interface

## API Reference

### Production Deployment Checklist

- [ ] HTTPS enabled on all routes
- [ ] CORS properly configured for mobile domain
- [ ] Rate limiting implemented on scan endpoints
- [ ] Activity logging enabled and monitored
- [ ] Barcode field indexed in database (Produit.code_produit, DemandeIntervention.nd)
- [ ] JWT secret key configured via environment variable
- [ ] Mobile cache TTL optimized for network conditions
- [ ] Backup/recovery procedure for activity logs
- [ ] User training completed for scanner interface
- [ ] Mobile device certificate pinning (optional, for security)

## Support & Escalation

### Common Issues

| Issue | Cause | Resolution |
|-------|-------|-----------|
| "Camera non disponible" | Browser permission denied | Grant camera permission in settings |
| "Barcode introuvable" | Product not in database | Add product with matching barcode |
| "Accès non autorisé" | User role insufficient | Contact administrator |
| 401 Unauthorized | Token expired | Re-login to refresh token |
| Duplicate scans | Network latency | Increase debounce time (adjust `SCAN_DEBOUNCE_MS`) |

## References

- [Quagga2 Documentation](https://serratus.github.io/quagga2/)
- [Flask-APScheduler](https://github.com/viniciuschiele/flask-apscheduler)
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [WebRTC API](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)

---

**Last Updated**: 2024-01-15
**Sprint**: 2
**Status**: ✅ COMPLETE
