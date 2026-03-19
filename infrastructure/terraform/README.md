# Digital Bank - Infrastructure as Code (Terraform)

This directory contains Terraform configurations for deploying the Digital Bank application to AWS.

## Structure

```
infrastructure/
└── terraform/
    ├── modules/
    │   ├── backend/        # ECS Fargate backend service
    │   ├── frontend/       # S3 + CloudFront frontend
    │   ├── postgres/        # RDS PostgreSQL with read replica
    │   └── redis/           # ElastiCache Redis
    └── environments/
        ├── staging/          # Staging environment
        └── production/       # Production environment
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0 installed
3. **S3 bucket** for Terraform state (created manually or via separate Terraform)

## Quick Start

### 1. Initialize Terraform

```bash
cd infrastructure/terraform/environments/staging
terraform init
```

### 2. Create S3 bucket for state (if not exists)

```bash
aws s3 mb s3://digital-bank-terraform-state-staging
```

### 3. Configure variables

Create a `terraform.tfvars` file:

```hcl
region = "us-east-1"
vpc_id = "vpc-xxxxx"
private_subnet_ids = ["subnet-xxxx", "subnet-xxxx"]
public_subnet_ids = ["subnet-xxxx", "subnet-xxxx"]
db_username = "bankadmin"
db_password = "your-secure-password"
secret_key = "your-jwt-secret-key"
backend_image = "ghcr.io/digital-bank/backend:latest"
```

### 4. Deploy

```bash
# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan
```

## Modules

### Backend Module
Deploys FastAPI backend on AWS ECS Fargate with:
- Application Load Balancer
- Auto-scaling (configurable desired count)
- Health checks
- CloudWatch logging
- Environment variable configuration (SECRET_KEY, DATABASE_URL, etc.)

### Frontend Module
Deploys React frontend on S3 with CloudFront:
- Static website hosting
- CloudFront CDN with HTTPS
- Cache invalidation support
- SPA routing support (index.html as default)

### PostgreSQL Module
Creates RDS PostgreSQL with:
- Read replica for analytics queries
- Multi-AZ support (production)
- Automated backups
- Encryption at rest
- Performance Insights (production)

### Redis Module
Creates ElastiCache Redis with:
- Optional encryption
- Snapshot retention (production)
- Automatic failover (production)

## Environments

### Staging
- Smaller instance sizes (db.t3, cache.t3)
- Single-AZ PostgreSQL
- 2 backend tasks
- Short backup retention

### Production
- Larger instance sizes (db.r6g, cache.r6g)
- Multi-AZ PostgreSQL with read replica
- 4+ backend tasks
- 30-day backup retention
- Deletion protection

## Security Considerations

1. **Secrets Management**: In production, use AWS Secrets Manager instead of terraform variables
2. **Network Isolation**: All services run in private subnets
3. **Encryption**: All data encrypted at rest and in transit
4. **Security Groups**: Minimal required ports only

## Maintenance

### Updating Infrastructure
```bash
terraform plan -out=tfplan
terraform apply tfplan
```

### Destroying Environment
```bash
terraform destroy
```

## CI/CD Integration

The Terraform configurations are designed to work with GitHub Actions:

1. Plan on PR to `develop` or `main`
2. Apply on merge to `develop` (staging) or `main` (production)

See `.github/workflows/ci.yml` for the full pipeline.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CloudFront                          │
└─────────────────────────────────────────────────────────────┘
                    │                        │
                    ▼                        ▼
           ┌──────────────┐         ┌──────────────┐
           │    S3       │         │     ALB      │
           │  (Frontend) │         │  (Backend)   │
           └──────────────┘         └──────────────┘
                                             │
                                             ▼
                                    ┌──────────────┐
                                    │    ECS       │
                                    │  (Fargate)   │
                                    └──────────────┘
                                       │        │
                              ┌────────┘        └────────┐
                              ▼                            ▼
                     ┌──────────────┐           ┌──────────────┐
                     │ PostgreSQL   │           │    Redis     │
                     │   (Primary)  │           │  ElastiCache │
                     └──────────────┘           └──────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │ PostgreSQL   │
                     │  (Replica)   │
                     └──────────────┘
```
