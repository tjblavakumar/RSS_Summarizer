@echo off
echo Uploading RSS Summarizer to EC2...

REM Create deployment package
echo Creating deployment package...
tar -czf rss-summarizer.tar.gz *.py templates/ static/ requirements.txt

REM Upload to EC2
echo Uploading files to EC2...
scp -i openhands-key.pem rss-summarizer.tar.gz ec2-user@44.205.255.62:/tmp/

REM Connect and deploy
echo Connecting to EC2 to deploy...
ssh -i openhands-key.pem ec2-user@44.205.255.62 "
    cd /tmp
    sudo mkdir -p /opt/rss-summarizer
    sudo tar -xzf rss-summarizer.tar.gz -C /opt/rss-summarizer
    sudo chown -R ec2-user:ec2-user /opt/rss-summarizer
    cd /opt/rss-summarizer
    
    # Install dependencies
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
    sudo systemctl restart rss-summarizer
    
    echo 'Deployment complete!'
    echo 'App running at: http://44.205.255.62:5000'
"

echo Deployment finished!
pause