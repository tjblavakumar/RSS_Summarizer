# RSS Summarizer - AWS Deployment Guide

This guide will help you deploy the RSS Summarizer webapp in a Docker container on an EC2 instance using Terraform.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured (`aws configure`)
3. **Terraform** installed (version 1.0+)
4. **SSH client** for connecting to EC2 instance

## Quick Deployment

### Option 1: Automated Script (Recommended)

**For Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**For Windows:**
```cmd
deploy.bat
```

### Option 2: Manual Deployment

1. **Generate SSH Key Pair:**
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/rss_summarizer_key
```

2. **Configure Terraform Variables:**
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your public key
```

3. **Deploy Infrastructure:**
```bash
terraform init
terraform plan
terraform apply
```

4. **Get Instance IP:**
```bash
terraform output public_ip
```

## Post-Deployment Setup

After Terraform completes, follow these steps:

1. **Wait for Instance Initialization** (2-3 minutes)

2. **Copy Application Files:**
```bash
scp -i ~/.ssh/rss_summarizer_key -r ./* ec2-user@<PUBLIC_IP>:/home/ec2-user/rss-app/
```

3. **SSH into Instance:**
```bash
ssh -i ~/.ssh/rss_summarizer_key ec2-user@<PUBLIC_IP>
```

4. **Build and Run Container:**
```bash
cd /home/ec2-user/rss-app
sudo docker-compose up -d
```

5. **Access Application:**
Open browser to `http://<PUBLIC_IP>`

## Configuration

### AWS Credentials
The EC2 instance has an IAM role with Bedrock permissions. No additional AWS configuration needed.

### Application Settings
- Default port: 80 (mapped from container port 5000)
- Database: SQLite (persistent via Docker volume)
- Logs: Available via `sudo docker-compose logs`

## Infrastructure Details

### Resources Created:
- **VPC** with public subnet
- **EC2 Instance** (t3.small by default)
- **Security Group** (ports 80, 22)
- **IAM Role** with Bedrock permissions
- **Internet Gateway** and routing

### Estimated Costs:
- **EC2 t3.small**: ~$15/month
- **Data Transfer**: Minimal for typical usage
- **AWS Bedrock**: Pay per API call (~$0.0005 per article)

## Management Commands

### View Application Logs:
```bash
ssh -i ~/.ssh/rss_summarizer_key ec2-user@<PUBLIC_IP>
sudo docker-compose logs -f
```

### Restart Application:
```bash
sudo docker-compose restart
```

### Update Application:
```bash
# Copy new files
scp -i ~/.ssh/rss_summarizer_key -r ./* ec2-user@<PUBLIC_IP>:/home/ec2-user/rss-app/
# Rebuild and restart
ssh -i ~/.ssh/rss_summarizer_key ec2-user@<PUBLIC_IP>
cd /home/ec2-user/rss-app
sudo docker-compose down
sudo docker-compose up -d --build
```

### Destroy Infrastructure:
```bash
cd terraform
terraform destroy
```

## Troubleshooting

### Common Issues:

1. **Application not accessible:**
   - Check security group allows port 80
   - Verify Docker container is running: `sudo docker ps`

2. **AWS Bedrock errors:**
   - Ensure IAM role has `bedrock:InvokeModel` permission
   - Check AWS region supports Claude 3 Haiku model

3. **Database issues:**
   - Database persists in Docker volume
   - Reset: `sudo docker-compose down -v && sudo docker-compose up -d`

### Logs and Debugging:
```bash
# Application logs
sudo docker-compose logs web

# System logs
sudo journalctl -u docker

# Container status
sudo docker ps -a
```

## Security Considerations

- **SSH Access**: Only use key-based authentication
- **Application**: Runs on port 80 (HTTP only)
- **Database**: Local SQLite, not exposed externally
- **AWS**: IAM role follows least-privilege principle

## Customization

### Change Instance Type:
Edit `terraform/terraform.tfvars`:
```hcl
instance_type = "t3.medium"  # or t3.large, etc.
```

### Change Region:
Edit `terraform/terraform.tfvars`:
```hcl
aws_region = "us-west-2"
```

### Add HTTPS:
Consider adding an Application Load Balancer with SSL certificate for production use.

## Support

For issues:
1. Check application logs
2. Verify AWS permissions
3. Ensure all prerequisites are met
4. Review Terraform output for errors