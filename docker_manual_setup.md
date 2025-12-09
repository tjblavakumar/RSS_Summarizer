# Manual Docker Setup on EC2

## 1. Connect to EC2
```bash
ssh -i openhands-key.pem ec2-user@44.205.255.62
```

## 2. Install Docker
```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user
```

## 3. Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 4. Upload Files
From Windows:
```cmd
scp -i openhands-key.pem -r . ec2-user@44.205.255.62:~/rss-summarizer/
```

## 5. Set AWS Credentials
```bash
cd ~/rss-summarizer
nano .env
```
Add:
```
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

## 6. Deploy
```bash
docker-compose up -d
```

## 7. Access
http://44.205.255.62:5000