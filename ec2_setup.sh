#!/bin/bash
# Run this script on EC2 instance to set up the environment

echo "Setting up RSS Summarizer on EC2..."

# Update system
sudo yum update -y

# Install Python 3.9 and development tools
sudo yum install -y python3 python3-pip git gcc python3-devel

# Install AWS CLI (if not already installed)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials (you'll need to run aws configure separately)
echo "Remember to run 'aws configure' to set up AWS credentials for Bedrock access"

# Open port 5000 in security group (if needed)
echo "Make sure port 5000 is open in your EC2 security group"

echo "EC2 setup complete!"
echo "Now upload your application files and run the deployment script"