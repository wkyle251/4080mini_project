#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting deployment on macOS..."

# Install required software
# echo "Installing required packages..."
# brew install redis nginx python3

# # Install Python dependencies
# echo "Installing Python dependencies..."
# pip3 install flask redis gunicorn torch torchvision

# # Set up Redis
# echo "Starting Redis server..."
# brew services start redis

# Create application directories
echo "Setting up application directories..."
APP_DIR="$HOME/image_classifier"
mkdir -p "$APP_DIR"
cp *.py "$APP_DIR"  # Copy Python scripts to the application directory

# Set up Gunicorn
echo "Creating Gunicorn startup script..."
cat > "$APP_DIR/gunicorn_start.sh" <<EOF
#!/bin/bash
cd $APP_DIR
exec gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
EOF
chmod +x "$APP_DIR/gunicorn_start.sh"

# Create a launchd plist file for Gunicorn
echo "Creating LaunchAgent for Gunicorn..."
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.image_classifier.gunicorn.plist"
cat > "$LAUNCH_AGENT" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.image_classifier.gunicorn</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_DIR/gunicorn_start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load the Gunicorn service
echo "Loading Gunicorn service..."
launchctl load -w "$LAUNCH_AGENT"

# Configure Nginx
echo "Configuring Nginx..."
NGINX_CONF="/usr/local/etc/nginx/servers/image_classifier.conf"
sudo mkdir -p /usr/local/etc/nginx/servers/
sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Restart Nginx
echo "Starting Nginx..."
sudo nginx -s reload || sudo nginx

# Start Python background processes
echo "Starting background Python scripts..."
IMAGE_DOWNLOADER_LOG="$APP_DIR/image_downloader.log"
PREDICT_LOG="$APP_DIR/predict.log"

nohup python3 "$APP_DIR/image_downloader.py" > "$IMAGE_DOWNLOADER_LOG" 2>&1 &
nohup python3 "$APP_DIR/predict.py" > "$PREDICT_LOG" 2>&1 &

# Display final status
echo "Deployment complete!"
echo "Gunicorn is running on http://localhost/"
echo "Redis is running on port 8888."
echo "Nginx is proxying requests to Gunicorn."

# Display log instructions
echo "To view logs:"
echo "  - Gunicorn: tail -f $HOME/Library/Logs/com.image_classifier.gunicorn.log"
echo "  - Image Downloader: tail -f $IMAGE_DOWNLOADER_LOG"
echo "  - Predictor: tail -f $PREDICT_LOG"
