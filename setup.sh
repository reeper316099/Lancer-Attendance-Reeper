#!/bin/bash
# RFID Attendance System Setup Script
# Run this on your Raspberry Pi to set up the system

set -e  # Exit on error

echo "=================================="
echo "RFID Attendance System Setup"
echo "=================================="
echo ""

# Check if running on Raspberry Pi
if ! [ -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   The RFID scanner may not work properly"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "Step 2: Installing dependencies..."
sudo apt install -y python3 python3-pip python3-venv git

echo ""
echo "Step 3: Enabling SPI interface..."
if ! lsmod | grep -q spi_bcm2835; then
    echo "SPI not enabled. Enabling now..."
    sudo raspi-config nonint do_spi 0
    echo "✅ SPI enabled (reboot required after setup)"
else
    echo "✅ SPI already enabled"
fi

echo ""
echo "Step 4: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "Step 5: Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python packages installed"

echo ""
echo "Step 6: Testing RFID hardware (optional)..."
read -p "Do you want to test the RFID reader now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Place an RFID card on the reader..."
    timeout 10 python3 -c "
try:
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()
    print('Reading card...')
    id = reader.read_id()
    print(f'✅ Card detected! UID: {id}')
except Exception as e:
    print(f'❌ Error: {e}')
    print('Make sure RFID reader is connected properly')
" || echo "No card detected or timeout"
fi

echo ""
echo "Step 7: Setting up systemd services..."
read -p "Set up auto-start services? (recommended for production) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    WORK_DIR=$(pwd)
    
    # Web service
    sudo tee /etc/systemd/system/attendance-web.service > /dev/null <<EOF
[Unit]
Description=RFID Attendance Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$WORK_DIR/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # RFID service
    sudo tee /etc/systemd/system/attendance-rfid.service > /dev/null <<EOF
[Unit]
Description=RFID Scanner Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
Environment="PATH=$WORK_DIR/venv/bin"
ExecStart=$WORK_DIR/venv/bin/python3 rfid_scanner.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable attendance-web.service attendance-rfid.service
    
    echo "✅ Systemd services created and enabled"
    echo ""
    read -p "Start services now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start attendance-web.service attendance-rfid.service
        echo "✅ Services started"
    fi
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "🎉 Your RFID Attendance System is ready!"
echo ""
echo "📍 Getting your Pi's IP address..."
IP=$(hostname -I | awk '{print $1}')
echo "   IP Address: $IP"
echo ""
echo "🌐 Access your system at:"
echo "   http://$IP:5000"
echo ""
echo "👤 Default login credentials:"
echo "   Username: admin    Password: admin123"
echo "   Username: teacher  Password: teacher123"
echo ""
echo "⚠️  IMPORTANT: Change these passwords after first login!"
echo ""
echo "📖 For more information, see README.md"
echo ""

if ! lsmod | grep -q spi_bcm2835; then
    echo "⚠️  REMINDER: System needs to reboot to activate SPI"
    read -p "Reboot now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
fi

echo "🚀 To start manually:"
echo "   Terminal 1: source venv/bin/activate && python3 app.py"
echo "   Terminal 2: source venv/bin/activate && python3 rfid_scanner.py"
echo ""
echo "📊 View services status:"
echo "   sudo systemctl status attendance-web.service"
echo "   sudo systemctl status attendance-rfid.service"
echo ""
echo "Happy tracking! 🎓"
