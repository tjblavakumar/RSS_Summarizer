#!/bin/bash
# Setup script for RSS Summarizer on EC2

echo "Setting up RSS Summarizer application..."

# Create app directory
mkdir -p /home/ec2-user/rss-app
cd /home/ec2-user/rss-app

# Extract application files
unzip -o /home/ec2-user/rss-app.zip

# Create data directory for persistent storage
mkdir -p data

# Build and run Docker container
sudo docker-compose up -d --build

echo "Application setup complete!"
echo "The RSS Summarizer should be available at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"