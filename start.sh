#!/bin/bash
# Quick Start Script for RFID Attendance System

echo "=================================="
echo "RFID Attendance System - Quick Start"
echo "=================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   RFID hardware features may not work"
    echo ""
fi

# Initialize database
echo "📦 Initializing database..."
python3 models.py

if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed"
    exit 1
fi

echo "✓ Database created successfully"
echo ""

# Check if admin accounts exist
echo "🔍 Checking for admin accounts..."
python3 -c "import models; c = models.get_db().__enter__().cursor(); c.execute('SELECT COUNT(*) FROM admins'); print(c.fetchone()[0])" > /tmp/admin_count.txt
ADMIN_COUNT=$(cat /tmp/admin_count.txt)

if [ "$ADMIN_COUNT" -eq "0" ]; then
    echo ""
    echo "ℹ️  No admin accounts found"
    echo "   After starting the server, visit:"
    echo "   http://localhost:5000/setup-admin"
    echo "   to create your admin accounts"
    echo ""
fi

echo "=================================="
echo "Starting RFID Attendance System"
echo "=================================="
echo ""
echo "📡 Starting web server on port 5000..."
echo "   Access at: http://localhost:5000"
echo ""
echo "🔧 To start the RFID scanner in another terminal:"
echo "   python3 rfid_scanner.py"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask app
python3 app.py
