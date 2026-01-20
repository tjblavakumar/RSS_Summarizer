#!/bin/bash

# RSS Summarizer Deployment Script for EC2
echo "Starting RSS Summarizer deployment..."

# Update system
sudo yum update -y

# Install Python 3.9 and pip
sudo yum install -y python3 python3-pip git

# Install required system packages
sudo yum install -y gcc python3-devel

# Create application directory
sudo mkdir -p /opt/rss-summarizer
sudo chown ec2-user:ec2-user /opt/rss-summarizer
cd /opt/rss-summarizer

# Copy application files (assuming files are uploaded)
echo "Application files should be uploaded to /opt/rss-summarizer"

# Install Python dependencies
pip3 install --user -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/rss-summarizer.service > /dev/null <<EOF
[Unit]
Description=RSS Summarizer Flask App
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/rss-summarizer
Environment=PATH=/home/ec2-user/.local/bin
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable rss-summarizer
sudo systemctl start rss-summarizer

# Configure firewall (if needed)
sudo firewall-cmd --permanent --add-port=5000/tcp 2>/dev/null || echo "Firewall not configured"
sudo firewall-cmd --reload 2>/dev/null || echo "Firewall not reloaded"

echo "Deployment complete! App should be running on port 5000"
echo "Access at: http://44.205.255.62:5000"