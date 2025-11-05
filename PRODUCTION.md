# Production Deployment Guide

Guide for deploying the voice agent to production for 100+ concurrent calls.

## Table of Contents
1. [Production Architecture](#production-architecture)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Deployment Steps](#deployment-steps)
4. [Security](#security)
5. [Monitoring](#monitoring)
6. [Maintenance](#maintenance)

---

## Production Architecture

### Recommended Setup

```
Internet
   │
   ▼
┌──────────────────┐
│  Load Balancer   │ ◄── AWS ALB / nginx
│  (with SSL)      │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│Webhook │ │Webhook │  ◄── Auto-scaling group
│   #1   │ │   #2   │
└────────┘ └────────┘
    │         │
    └────┬────┘
         │
         ▼
┌──────────────────┐
│  LiveKit Cloud   │  ◄── Managed service
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Agent  │ │ Agent  │  ◄── Auto-scaling group
│   #1   │ │   #2   │
└────────┘ └────────┘
```

---

## Infrastructure Setup

### Option 1: AWS Deployment (Recommended)

#### Prerequisites
- AWS Account
- AWS CLI configured
- Docker installed
- Domain name

#### 1. Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets (2 for redundancy)
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 --availability-zone us-east-1a
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 --availability-zone us-east-1b

# Create internet gateway
aws ec2 create-internet-gateway
aws ec2 attach-internet-gateway --vpc-id vpc-xxx --internet-gateway-id igw-xxx
```

#### 2. Create Security Groups

```bash
# Webhook server security group
aws ec2 create-security-group \
    --group-name webhook-sg \
    --description "Webhook server security group" \
    --vpc-id vpc-xxx

# Allow HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow HTTP (for health checks)
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxx \
    --protocol tcp \
    --port 8000 \
    --cidr 10.0.0.0/16
```

#### 3. Create Launch Template for Webhook Servers

```bash
# Create webhook-server-template.yaml
cat > webhook-server-template.yaml << 'EOF'
#!/bin/bash
# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.9+
apt-get install -y python3.9 python3.9-venv python3-pip

# Clone your repository
cd /opt
git clone https://github.com/your-repo/voice-agent.git
cd voice-agent

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from Secrets Manager
aws secretsmanager get-secret-value --secret-id voice-agent-config --query SecretString --output text > .env

# Start webhook server with systemd
cat > /etc/systemd/system/webhook.service << 'SERVICE'
[Unit]
Description=Voice Agent Webhook Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/voice-agent
Environment="PATH=/opt/voice-agent/venv/bin"
ExecStart=/opt/voice-agent/venv/bin/python webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable webhook
systemctl start webhook
EOF

# Create launch template
aws ec2 create-launch-template \
    --launch-template-name webhook-server \
    --version-description "Webhook server v1" \
    --launch-template-data file://webhook-server-template.yaml
```

#### 4. Create Auto Scaling Group

```bash
# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name webhook-asg \
    --launch-template LaunchTemplateName=webhook-server \
    --min-size 2 \
    --max-size 10 \
    --desired-capacity 2 \
    --vpc-zone-identifier "subnet-xxx,subnet-yyy" \
    --target-group-arns arn:aws:elasticloadbalancing:...

# Create scaling policies
aws autoscaling put-scaling-policy \
    --auto-scaling-group-name webhook-asg \
    --policy-name scale-up \
    --policy-type TargetTrackingScaling \
    --target-tracking-configuration file://scale-up-policy.json
```

#### 5. Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name voice-agent-alb \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-xxx \
    --scheme internet-facing

# Create target group
aws elbv2 create-target-group \
    --name webhook-targets \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxx \
    --health-check-path /health

# Create listener
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:... \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=arn:aws:acm:... \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

#### 6. Setup Agent Workers (Similar to webhook servers)

Create separate Auto Scaling Group for agent workers.

---

### Option 2: Google Cloud Platform

#### Using Cloud Run (Serverless)

```bash
# Build Docker image
docker build -t gcr.io/PROJECT_ID/voice-agent:latest .

# Push to Container Registry
docker push gcr.io/PROJECT_ID/voice-agent:latest

# Deploy to Cloud Run
gcloud run deploy voice-agent \
    --image gcr.io/PROJECT_ID/voice-agent:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --min-instances 2 \
    --max-instances 100 \
    --concurrency 80 \
    --memory 2Gi \
    --cpu 2
```

---

### Option 3: Docker Compose (Simple Production)

```yaml
# docker-compose.yml
version: '3.8'

services:
  webhook:
    build: .
    command: python webhook_server.py
    ports:
      - "8000:8000"
    env_file: .env
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  agent:
    build: .
    command: python agent.py
    env_file: .env
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '4'
          memory: 8G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - webhook
    restart: always
```

Deploy:
```bash
docker-compose up -d --scale agent=5
```

---

## Deployment Steps

### 1. Prepare Environment

```bash
# Clone repository
git clone https://github.com/your-repo/voice-agent.git
cd voice-agent

# Create production .env
cp env.example .env.production
nano .env.production
```

### 2. Setup SSL Certificate

```bash
# Using Let's Encrypt with certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Certificate will be in:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 3. Configure nginx (Reverse Proxy)

```nginx
# /etc/nginx/sites-available/voice-agent
upstream webhook_servers {
    least_conn;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Webhook endpoint
    location /incoming-call {
        proxy_pass http://webhook_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://webhook_servers;
        access_log off;
    }

    # Metrics (restrict access)
    location /metrics {
        proxy_pass http://webhook_servers;
        allow 10.0.0.0/8;  # Internal network only
        deny all;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/voice-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Configure Twilio

Update Twilio webhook to production URL:
```
https://your-domain.com/incoming-call
```

### 5. Setup Monitoring

Install monitoring tools:
```bash
# Prometheus
docker run -d -p 9090:9090 prom/prometheus

# Grafana
docker run -d -p 3000:3000 grafana/grafana
```

---

## Security

### 1. Secure Environment Variables

Use secrets management:

#### AWS Secrets Manager
```bash
aws secretsmanager create-secret \
    --name voice-agent-config \
    --secret-string file://.env
```

Retrieve in code:
```python
import boto3
import json

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='voice-agent-config')
    return json.loads(response['SecretString'])
```

### 2. Twilio Request Validation

Add to `webhook_server.py`:
```python
from twilio.request_validator import RequestValidator

validator = RequestValidator(Config.TWILIO_AUTH_TOKEN)

@app.post("/incoming-call")
async def incoming_call(request: Request):
    # Validate request is from Twilio
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    params = await request.form()
    
    if not validator.validate(url, params, signature):
        logger.warning(f"Invalid Twilio signature from {request.client.host}")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # ... rest of code
```

### 3. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/incoming-call")
@limiter.limit("100/minute")  # Max 100 calls per minute per IP
async def incoming_call(request: Request):
    # ... code
```

### 4. Firewall Rules

```bash
# Only allow specific ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

## Monitoring

### 1. Application Metrics

Add to your code:
```python
from prometheus_client import Counter, Histogram, Gauge

# Metrics
calls_total = Counter('calls_total', 'Total calls processed')
call_duration = Histogram('call_duration_seconds', 'Call duration')
active_calls = Gauge('active_calls', 'Currently active calls')
errors_total = Counter('errors_total', 'Total errors', ['type'])

# Usage
@app.post("/incoming-call")
async def incoming_call(request: Request):
    calls_total.inc()
    active_calls.inc()
    
    start_time = time.time()
    try:
        # ... handle call
        pass
    except Exception as e:
        errors_total.labels(type=type(e).__name__).inc()
        raise
    finally:
        duration = time.time() - start_time
        call_duration.observe(duration)
        active_calls.dec()
```

### 2. Log Aggregation

Use ELK Stack (Elasticsearch, Logstash, Kibana) or CloudWatch:

```python
import logging
from pythonjsonlogger import jsonlogger

# JSON logging for better parsing
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
```

### 3. Alerting

Setup alerts in CloudWatch/Prometheus:
```yaml
# alerting-rules.yml
groups:
  - name: voice_agent
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        annotations:
          summary: "Error rate above 5%"
      
      - alert: HighLatency
        expr: histogram_quantile(0.95, call_duration_seconds) > 2
        annotations:
          summary: "95th percentile latency above 2s"
      
      - alert: HighConcurrency
        expr: active_calls > 140
        annotations:
          summary: "Active calls approaching limit"
```

---

## Maintenance

### 1. Backup

```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz \
    .env \
    config.py \
    webhook_server.py \
    agent.py

# Upload to S3
aws s3 cp backup-*.tar.gz s3://your-backup-bucket/
```

### 2. Updates

```bash
# Zero-downtime deployment
# 1. Deploy to staging
git pull origin main
pip install -r requirements.txt

# 2. Test staging
python test_setup.py

# 3. Rolling update production
# Update instances one by one
for instance in $(aws ec2 describe-instances ...); do
    # Update instance
    ssh $instance "cd /opt/voice-agent && git pull && sudo systemctl restart webhook"
    # Wait for health check
    sleep 30
done
```

### 3. Database Maintenance (if added)

```bash
# Backup database
pg_dump voice_agent > backup-$(date +%Y%m%d).sql

# Vacuum and analyze
psql voice_agent -c "VACUUM ANALYZE;"
```

---

## Cost Optimization

### 1. Reserved Instances

For predictable load, buy reserved instances:
- AWS EC2 Reserved Instances (up to 72% savings)
- 1-year or 3-year terms

### 2. Spot Instances

For agent workers (fault-tolerant):
```bash
aws ec2 request-spot-instances \
    --spot-price "0.05" \
    --instance-count 5 \
    --type "one-time" \
    --launch-specification file://spot-spec.json
```

### 3. Auto-scaling

Scale down during off-peak hours:
```bash
# Scheduled scaling
aws autoscaling put-scheduled-update-group-action \
    --auto-scaling-group-name webhook-asg \
    --scheduled-action-name scale-down-night \
    --recurrence "0 2 * * *" \
    --desired-capacity 2
```

---

## Checklist

### Pre-deployment
- [ ] Code tested with load tests
- [ ] All credentials in secrets manager
- [ ] SSL certificates obtained
- [ ] Domain DNS configured
- [ ] Monitoring setup
- [ ] Alerting configured
- [ ] Backup strategy in place

### Deployment
- [ ] Infrastructure provisioned
- [ ] Load balancer configured
- [ ] Auto-scaling groups created
- [ ] Services deployed
- [ ] Health checks passing
- [ ] Twilio webhook updated

### Post-deployment
- [ ] Test calls successful
- [ ] Monitoring showing data
- [ ] Logs being collected
- [ ] Performance within SLA
- [ ] Alerts working
- [ ] Documentation updated

---

## Support

For production issues:
- Check monitoring dashboards first
- Review application logs
- Check AWS/GCP console for infrastructure issues
- Contact LiveKit support if needed
- Review Twilio debugger for call issues

---

Ready for production! 🚀

