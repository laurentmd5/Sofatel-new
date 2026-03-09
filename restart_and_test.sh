#!/bin/bash
# Test KPI Dashboard

echo "🔄 Restarting Flask server..."
kill $(lsof -t -i:5000) 2>/dev/null || true
sleep 2

cd ~/OneDrive/Documents/SOFATELCOM-V2/SOFATELCOM-V2

echo "✅ Starting Flask..."
flask run --host=0.0.0.0 &
FLASK_PID=$!

sleep 5

echo "🧪 Testing endpoints..."
echo ""
echo "1. Testing Dashboard KPI access..."
curl -s -b "test_session=1" "http://localhost:5000/dashboard/kpi" | grep -q "Dashboard KPI" && echo "✅ Dashboard KPI loads" || echo "❌ Dashboard KPI failed"

echo ""
echo "2. Testing KPI API endpoints..."
curl -s "http://localhost:5000/api/kpi/metrics" | grep -q "data" && echo "✅ API metrics endpoint works" || echo "❌ API metrics endpoint failed"

echo ""
echo "3. Server is running on port 5000"
echo "   - Local: http://127.0.0.1:5000"
echo "   - Network: http://192.168.1.25:5000"
echo ""
echo "✅ Ready for testing!"
echo ""
echo "Press CTRL+C to stop"

wait $FLASK_PID
