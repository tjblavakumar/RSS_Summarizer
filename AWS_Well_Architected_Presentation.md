# Daily News AI Assistant
## AWS Well-Architected Framework Alignment

---

## Architecture Overview

**System:** Daily News AI Assistant - RSS Aggregation & AI Summarization

**Deployment:**
- EC2 instance in private subnet
- Application Load Balancer (ALB) in public subnet
- Route 53 for DNS
- AWS Bedrock for AI processing
- Internet Gateway for external RSS feeds

---

## 1. Operational Excellence

### Design Principles Met

**Infrastructure as Code**
- Terraform configuration for reproducible deployments
- Version-controlled infrastructure in `/terraform` directory
- Automated deployment scripts

**Monitoring & Logging**
- Application logs for debugging and troubleshooting
- CloudWatch integration capability for EC2 metrics
- ALB access logs for traffic analysis

**Automation**
- Automated RSS feed processing with scheduler
- Auto-refresh dashboard (10-second intervals)
- Automated article cleanup (24-hour retention)

**Continuous Improvement**
- Modular Python architecture for easy updates
- Database migration scripts for schema evolution
- Configuration management via environment variables

---

## 2. Security

### Design Principles Met

**Defense in Depth**
- Private subnet deployment for application tier
- Security groups restricting traffic:
  - ALB SG: Port 443 from internet (0.0.0.0/0)
  - EC2 SG: Port 5000 from ALB only
- Network isolation via VPC

**Identity & Access Management**
- IAM role attached to EC2 instance
- Least privilege: `bedrock:InvokeModel` permission only
- No hardcoded credentials in application code

**Data Protection**
- HTTPS/TLS for all external communications
- SSL termination at ALB
- Encrypted communication with AWS Bedrock

**Security Best Practices**
- No public IP on EC2 instance
- Internet access via NAT/Internet Gateway only
- Secrets management via environment variables
- Input validation on RSS feed URLs

---

## 3. Reliability

### Design Principles Met

**Fault Tolerance**
- ALB health checks for EC2 instance availability
- Graceful error handling in application code
- Retry logic for external API calls (RSS feeds, Bedrock)

**Recovery Procedures**
- Database backup capability (SQLite file-based)
- Automated article cleanup prevents storage exhaustion
- Application restart capability via systemd/supervisor

**Scalability Foundation**
- Stateless application design
- Ready for horizontal scaling with multiple EC2 instances
- ALB supports multiple targets for future expansion

**Change Management**
- Database migration scripts for safe schema updates
- Version-controlled codebase
- Rollback capability via Terraform state

**Monitoring**
- Application-level error logging
- CloudWatch metrics for EC2 health
- ALB metrics for request tracking

---

## 4. Performance Efficiency

### Design Principles Met

**Right-Sizing Resources**
- t3.medium EC2 instance (cost-effective for workload)
- Claude 3 Haiku model (fast, low-latency AI processing)
- SQLite for lightweight data storage needs

**Efficient Architecture**
- Single AI call per article for all topics (batch processing)
- Content truncation to 3000 chars (optimized token usage)
- Auto-refresh reduces manual user actions

**Caching & Optimization**
- 24-hour article retention (prevents reprocessing)
- Unique URL constraints (no duplicate processing)
- Efficient database queries with SQLAlchemy ORM

**Managed Services**
- AWS Bedrock (no infrastructure management)
- ALB (managed load balancing)
- Route 53 (managed DNS)

**Performance Monitoring**
- Response time tracking capability
- Bedrock API latency monitoring
- Database query performance optimization

---

## 5. Cost Optimization

### Design Principles Met

**Right-Sizing**
- Single t3.medium EC2 instance (~$30/month)
- Claude 3 Haiku: ~$0.25 per 1M tokens (most cost-effective)
- Estimated cost: $0.0005-0.001 per article

**Pay-for-Use**
- AWS Bedrock: Pay only for API calls made
- No idle AI infrastructure costs
- ALB charges only for active usage

**Resource Optimization**
- Automatic article cleanup (24 hours) reduces storage
- Content truncation reduces Bedrock token costs
- Single AI call per article (efficient batch scoring)

**Cost Monitoring**
- CloudWatch for usage tracking
- Bedrock API call metrics
- Potential for AWS Cost Explorer integration

**Reserved Capacity (Future)**
- EC2 Reserved Instances for predictable workloads
- Savings Plans for long-term commitment

---

## 6. Sustainability

### Design Principles Met

**Efficient Resource Utilization**
- Single EC2 instance for low-traffic workload
- Serverless AI via Bedrock (no idle compute)
- Lightweight SQLite database (no separate DB server)

**Minimize Data Movement**
- Local SQLite storage on EC2 (no network DB calls)
- Content truncation reduces data transfer
- Efficient JSON responses from Bedrock

**Optimize for Workload**
- Claude 3 Haiku: Smallest, most efficient model
- Batch processing of topics (single API call)
- Auto-cleanup prevents unnecessary storage growth

**Managed Services**
- AWS Bedrock: Shared infrastructure, better utilization
- ALB: Efficient traffic distribution
- Route 53: Global DNS with minimal carbon footprint

**Future Improvements**
- Consider AWS Graviton instances (better performance/watt)
- Implement caching to reduce redundant API calls
- Schedule processing during off-peak hours

---

## Architecture Diagram

```
Internet Users
      ↓
  Route 53 (DNS)
      ↓
┌─────────────────────────────────────────┐
│           AWS Cloud                      │
│                                          │
│  ┌────────────────┐                     │
│  │  Public Subnet │                     │
│  │                │                     │
│  │  ┌──────────┐  │                     │
│  │  │   ALB    │  │                     │
│  │  │ (Port 443)│ │                     │
│  │  └─────┬────┘  │                     │
│  └────────┼───────┘                     │
│           │                              │
│  ┌────────┼──────────────────┐          │
│  │ Private│Subnet            │          │
│  │        ↓                  │          │
│  │  ┌──────────┐             │          │
│  │  │   EC2    │─────────────┼──→ AWS Bedrock
│  │  │  Flask   │             │   (Claude 3 Haiku)
│  │  │  App     │             │          │
│  │  └────┬─────┘             │          │
│  │       │                   │          │
│  │  ┌────┴─────┐             │          │
│  │  │ SQLite   │             │          │
│  │  │   DB     │             │          │
│  │  └──────────┘             │          │
│  └───────────────────────────┘          │
│           │                              │
│    Internet Gateway                      │
│           │                              │
└───────────┼──────────────────────────────┘
            ↓
    External RSS Feeds
    (BBC, Reuters, CNN)
```

---

## Summary: Well-Architected Compliance

| Pillar | Compliance Level | Key Implementations |
|--------|-----------------|---------------------|
| **Operational Excellence** | ✅ High | IaC (Terraform), automation, monitoring |
| **Security** | ✅ High | Private subnet, IAM roles, security groups, TLS |
| **Reliability** | ✅ Medium | ALB health checks, error handling, backups |
| **Performance Efficiency** | ✅ High | Right-sized resources, efficient AI model, caching |
| **Cost Optimization** | ✅ High | Pay-per-use, efficient model, auto-cleanup |
| **Sustainability** | ✅ Medium | Managed services, efficient compute, minimal data movement |

---

## Recommendations for Enhancement

### Reliability
- Add Auto Scaling Group for high availability
- Implement multi-AZ deployment
- Use RDS instead of SQLite for durability

### Security
- Enable AWS WAF on ALB
- Implement AWS Secrets Manager for credentials
- Enable VPC Flow Logs

### Performance
- Add CloudFront CDN for static assets
- Implement ElastiCache for session management
- Use Aurora Serverless for database scaling

### Cost
- Implement EC2 Reserved Instances
- Use S3 for article archival (cheaper than EC2 storage)
- Set up AWS Budgets and alerts

---

## Contact & Documentation

**Project Repository:** RSS_Summarizer  
**Architecture Diagrams:** C4 Models (Level 1-3)  
**Deployment:** Terraform IaC in `/terraform`  
**Documentation:** README.md, DEPLOYMENT.md

**AWS Services Used:**
- EC2, VPC, ALB, Route 53
- AWS Bedrock (Claude 3 Haiku)
- IAM, Security Groups
- Internet Gateway

---
