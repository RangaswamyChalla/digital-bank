# Digital Bank - Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Digital Bank application.

## Structure

```
infrastructure/k8s/
├── namespace.yaml    # Namespace and base config
├── postgres.yaml     # PostgreSQL StatefulSet
├── redis.yaml       # Redis deployment
├── backend.yaml     # FastAPI backend deployment
├── worker.yaml      # ARQ background worker
└── kustomization.yaml  # Kustomize configuration
```

## Prerequisites

1. Kubernetes cluster (1.25+)
2. kubectl configured
3. Optional: External Secrets Operator for secrets management

## Quick Start

### 1. Create namespace and apply configurations

```bash
cd infrastructure/k8s
kubectl apply -k .
```

### 2. Or apply individual files

```bash
kubectl apply -f namespace.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f backend.yaml
kubectl apply -f worker.yaml
```

### 3. Check deployment status

```bash
kubectl get pods -n digital-bank
kubectl get services -n digital-bank
```

## Production Recommendations

### 1. External Secrets
For production, use External Secrets Operator to integrate with:
- AWS Secrets Manager
- HashiCorp Vault
- GCP Secret Manager

### 2. PostgreSQL High Availability
The included manifest is for single-instance PostgreSQL. For HA:
- Use CloudSQL (GCP), RDS (AWS), or Azure Database
- Or configure Patroni for self-managed HA

### 3. Redis
For production Redis:
- Use ElastiCache (AWS), Memorystore (GCP), or Azure Cache
- Or configure Redis Sentinel or Cluster

### 4. Ingress
For production, configure a proper ingress:
- AWS ALB Ingress Controller
- Nginx Ingress Controller
- Cert-manager for TLS

## Scaling

### Backend
```bash
kubectl scale deployment digital-bank-backend --replicas=5 -n digital-bank
```

### Workers
```bash
kubectl scale deployment digital-bank-worker --replicas=4 -n digital-bank
```

## Monitoring

Add Prometheus scraping to your pods:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```
