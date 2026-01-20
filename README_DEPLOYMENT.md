# RSS Summarizer - Docker & AWS Deployment

## Quick Start

Deploy your RSS Summarizer to AWS EC2 with Docker in 3 steps:

### 1. Prerequisites
- AWS CLI configured (`aws configure`)
- Terraform installed
- SSH client

### 2. Deploy
```bash
# Linux/Mac
./deploy.sh

# Windows
deploy.bat
```

### 3. Access
Your app will be available at `http://<PUBLIC_IP>` after deployment completes.

## What Gets Deployed

- **EC2 Instance** (t3.small) with Docker
- **VPC** with public subnet and security groups
- **IAM Role** with AWS Bedrock permissions
- **Containerized Flask App** on port 80

## Files Added for Deployment

```
RSS_Summarizer/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Local container orchestration
├── .dockerignore           # Docker build exclusions
├── deploy.sh/.bat          # Automated deployment scripts
├── DEPLOYMENT.md           # Detailed deployment guide
└── terraform/              # Infrastructure as Code
    ├── main.tf             # AWS resources
    ├── variables.tf        # Configuration variables
    ├── outputs.tf          # Deployment outputs
    ├── user_data.sh        # EC2 initialization script
    └── terraform.tfvars.example
```

## Cost Estimate
- **EC2 t3.small**: ~$15/month
- **AWS Bedrock**: ~$0.0005 per article analyzed
- **Data Transfer**: Minimal

## Next Steps
1. Run deployment script
2. Wait for completion (5-10 minutes)
3. Follow post-deployment instructions
4. Access your live RSS Summarizer!

See `DEPLOYMENT.md` for detailed instructions and troubleshooting.