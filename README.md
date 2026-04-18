# CI/CD–GitOps Framework: Experimental Data Collection
## IEEE Conference Paper — Complete Setup and Execution Guide

---

## RESEARCH OVERVIEW

### Title
An End-to-End CI/CD–GitOps Framework for Kubernetes-Based Microservices:
Architecture and Experimental Validation

### Research Objective
This project empirically validates a unified CI/CD–GitOps framework that integrates
Jenkins (continuous integration), Argo CD (GitOps-driven continuous delivery), and
Amazon EKS (managed Kubernetes) against a conventional Jenkins-only CI/CD baseline.

### Research Gaps Addressed
1. No prior work provides statistically rigorous comparison (Welch t-test, Cohen's d,
   Mann-Whitney U) of GitOps vs. imperative CI/CD on production-grade cloud infrastructure.
2. Configuration drift — the silent accumulation of out-of-band cluster modifications —
   has never been quantified with real timing data in an academic setting.
3. Chaos resilience of GitOps self-healing mechanisms has not been experimentally
   characterised against a baseline that has no self-healing capability.
4. Security (RBAC, IAM, ESO) and scalability (HPA, cluster autoscaling) have been
   treated separately in literature; this work integrates them into a single framework.

### Novel Contributions
1. Unified CI/CD–GitOps reference architecture on Amazon EKS with integrated
   security and horizontal scalability.
2. 25-run controlled experiment with full statistical analysis across deployment,
   drift correction, rollback, chaos resilience, and HPA dimensions.
3. First empirical quantification of Argo CD drift detection and correction latency
   by detection path (webhook vs. polling).
4. Chaos resilience experiment (pod-kill, replica-zero) as a novel fourth
   experimental dimension not present in prior GitOps benchmarks.
5. Raw CSV data (190+ logged data points) provided for independent reproducibility.

---

## CLUSTER DETAILS (your environment)

| Item | Value |
|---|---|
| Cluster name | kastro-cluster |
| Region | ap-south-1 (Mumbai) |
| Worker nodes | 2x t2.medium |
| Worker node IPs | 13.233.100.26, 43.204.25.49 |
| Worker security group | sg-03d98966b4e46b121 |
| Argo CD | Installed, all pods Running |
| Argo CD URL | ae7828c99d08d45a7a166f1392a8bec2-2128056202.ap-south-1.elb.amazonaws.com |
| DockerHub | kastrov |
| Client VM | Ubuntu 24.04, t2.medium |

---

## PROJECT STRUCTURE

```
kastro-project/
├── user-service/
│   ├── app.py              Flask REST API (User CRUD: GET/POST/DELETE)
│   ├── test_app.py         40 pytest tests (>85% coverage)
│   ├── requirements.txt    flask, pytest, pytest-cov
│   └── Dockerfile          Multi-stage build, non-root user, HEALTHCHECK
│
├── product-service/
│   ├── app.py              Flask REST API (Product catalogue: GET/POST/PUT)
│   ├── test_app.py         40 pytest tests (>85% coverage)
│   ├── requirements.txt
│   └── Dockerfile
│
├── k8s-manifests/
│   ├── namespaces/
│   │   └── production.yaml         Production namespace
│   ├── user-service/
│   │   └── deployment.yaml         Deployment + NodePort Service + HPA
│   ├── product-service/
│   │   └── deployment.yaml         Deployment + NodePort Service + HPA
│   └── argocd/
│       └── applications.yaml       Argo CD Application CRDs (selfHeal + prune)
│
├── scripts/
│   ├── stage1_setup.sh             Install deps, open security group
│   ├── stage2_build_push.sh        Build + push 6 image tags per service
│   ├── stage3_deploy.sh            Deploy to K8s + setup Argo CD
│   ├── stage4_experiments.py       Run all 6 experiments, write CSVs
│   └── stage5_analyze.py           Statistical analysis, paper-ready output
│
├── outputs/                        Created automatically — all data files
└── README.md                       This file
```

---

## TIME PLAN (fits in 120 minutes)

| Stage | Script | Est. Time | Cumulative |
|---|---|---|---|
| Stage 1 | stage1_setup.sh | 3 min | 3 min |
| Stage 2 | stage2_build_push.sh | 12 min | 15 min |
| Stage 3 | stage3_deploy.sh | 10 min | 25 min |
| Stage 4 | stage4_experiments.py | 75 min | 100 min |
| Stage 5 | stage5_analyze.py | 2 min | 102 min |
| Buffer | cleanup + download | 10 min | 112 min |

---

## STEP-BY-STEP EXECUTION

### PRE-REQUISITE: Create GitHub repo (do this NOW, before anything else)

1. Go to https://github.com/new
2. Repository name: `gitops-repo`
3. Visibility: **Public**
4. Check "Add a README file"
5. Click "Create repository"

### STEP 0: SSH into your EC2 client VM and prepare

```bash
# Use screen so SSH disconnect won't kill experiments
apt install screen -y
screen -S kastro
# (if reconnecting later: screen -r kastro)

# Clone or update this project
cd /home/ubuntu
# If you already have it cloned, just cd into it:
cd ML-Work   # or wherever you have the project
```

### STEP 1: Environment Setup

```bash
chmod +x scripts/stage1_setup.sh
./scripts/stage1_setup.sh
```

**What it does:**
- Installs pip3 and the `requests` Python library
- Opens NodePort range 30000-32767 on security group sg-03d98966b4e46b121
- Verifies kubectl cluster access
- Verifies Argo CD pods are running
- Saves environment config to outputs/env_info.txt

**Expected output ends with:**
```
============================================================
  STAGE 1 COMPLETE
  NEXT: Run ./stage2_build_push.sh
============================================================
```

---

### STEP 2: Build and Push Docker Images

```bash
chmod +x scripts/stage2_build_push.sh
./scripts/stage2_build_push.sh
```

**What it does:**
- Prompts you for DockerHub password (type it once)
- Builds 6 image tags for user-service: 1.0.0, 1.0.1, 1.0.2, 1.0.3, 1.0.4, 1.0.5
- Builds 6 image tags for product-service: same versions
- Pushes all 12 images to kastrov/ on DockerHub
- Runs all 40 unit tests for both services locally
- Saves outputs/images.txt

**Expected output ends with:**
```
============================================================
  STAGE 2 COMPLETE
  NEXT: Run ./stage3_deploy.sh
============================================================
```

---

### STEP 3: Deploy to Kubernetes and Setup Argo CD

**BEFORE running this script**, push the k8s-manifests to your gitops-repo:

```bash
# Run these commands from inside your project directory
cd /home/ubuntu/ML-Work   # adjust path as needed

# One-time Git identity setup (if not done)
git config --global user.email "kastro@experiment.com"
git config --global user.name "Kastro"

# Create local gitops directory
rm -rf /tmp/gitops-push
mkdir -p /tmp/gitops-push/k8s-manifests
cp -r k8s-manifests/user-service /tmp/gitops-push/k8s-manifests/
cp -r k8s-manifests/product-service /tmp/gitops-push/k8s-manifests/
cp -r k8s-manifests/namespaces /tmp/gitops-push/k8s-manifests/

cd /tmp/gitops-push
git init
git add .
git commit -m "Initial k8s manifests for CI/CD-GitOps experiment"
git branch -M main
git remote add origin https://github.com/KastroVKiran/gitops-repo.git
git push -u origin main
# Enter your GitHub username and Personal Access Token when prompted
# (Create PAT at: https://github.com/settings/tokens -> Generate new token -> repo scope)
```

Then run Stage 3:

```bash
cd /home/ubuntu/ML-Work   # back to project root
chmod +x scripts/stage3_deploy.sh
./scripts/stage3_deploy.sh
```

**What it does:**
- Creates production namespace
- Deploys user-service (2 replicas) + HPA
- Deploys product-service (2 replicas) + HPA
- Waits for pods to be Ready
- Tests health endpoints via curl
- Registers both services as Argo CD Applications
- Saves Argo CD password to outputs/deployment_info.txt

**The script will PAUSE and ask you to press Enter** after printing
the Argo CD password and URL. This is intentional — use that moment
to verify the health endpoints:

```bash
# Open a second terminal and test:
curl http://13.233.100.26:31096/health
curl http://13.233.100.26:31471/health
# Both should return: {"status": "healthy", ...}
```

Then press Enter in the Stage 3 terminal to continue.

**Expected output ends with:**
```
============================================================
  STAGE 3 COMPLETE
  NEXT: Run python3 scripts/stage4_experiments.py
============================================================
```

---

### STEP 4: Run All Experiments (THE MAIN DATA COLLECTION)

```bash
python3 scripts/stage4_experiments.py 2>&1 | tee outputs/stage4_run.log
```

**What it does (6 experiments, ~75 minutes total):**

| Experiment | What is measured | Rows |
|---|---|---|
| Exp 1: Proposed deployments | Build + push + Argo CD detect + sync + health | 25 |
| Exp 2: Baseline deployments | Build + push + kubectl deploy + rollout wait | 25 |
| Exp 3: Drift correction | Inject drift → detect → Argo CD auto-correct | 25 |
| Exp 4: Rollback | Bad deploy → rollback (proposed vs. baseline) | 50 |
| Exp 5: Chaos resilience | Pod kill / replica-zero → recovery timing | 20 |
| Exp 6: HPA scaling | Replica + CPU snapshots at various load levels | 60 |

**You will see progress like this:**
```
[2025-...Z] ==================================================
[2025-...Z]   EXPERIMENT 1: Proposed Framework — 25 deployment runs
[2025-...Z] ==================================================
[2025-...Z]   --- Run 1/25 | user-service | tag=1.0.0 ---
[2025-...Z]      build=67.3s push=38.2s detect=4.1s sync=12.3s TOTAL=2.031min
[2025-...Z]   --- Run 2/25 | product-service | tag=1.0.1 ---
...
```

**DO NOT close the terminal.** If SSH disconnects, reconnect and run:
```bash
screen -r kastro
```

**Expected final output:**
```
============================================================
  STAGE 4 COMPLETE
  FILES GENERATED (give ALL to Claude):
    exp1_proposed_deployments.csv  (XXX bytes)
    exp2_baseline_deployments.csv  (XXX bytes)
    exp3_drift_correction.csv      (XXX bytes)
    exp4_rollback.csv              (XXX bytes)
    exp5_chaos_resilience.csv      (XXX bytes)
    exp6_hpa_scaling.csv           (XXX bytes)
    stage4_run.log                 (XXX bytes)
  NEXT: Run python3 scripts/stage5_analyze.py
============================================================
```

---

### STEP 5: Statistical Analysis

```bash
python3 scripts/stage5_analyze.py
```

**What it does:**
- Reads all 6 CSV files
- Computes mean, SD, median, min-max, 95% CI for all metrics
- Runs Welch two-sample t-test, Cohen's d, Mann-Whitney U test
- Saves all paper-ready numbers to outputs/paper_statistics.txt

**Expected final output includes:**
```
TABLE I — DEPLOYMENT PERFORMANCE COMPARISON
  Proposed op. mean ± SD : X.XXX ± X.XXX min
  Baseline op. mean ± SD : X.XXX ± X.XXX min
  Welch t(XX) = X.XX, p = X.XXXXX, d = X.XX
...
```

---

### STEP 6: Download Output Files

```bash
# Verify all files exist and are non-empty
ls -lh outputs/

# Create zip for download
cd /home/ubuntu/ML-Work
zip -r experiment_results.zip outputs/
```

Then use SCP or your SSH client to download `experiment_results.zip` to your laptop,
and upload all files in the zip to Claude.

---

## WHAT DATA TO GIVE CLAUDE

Upload ALL of these files:
1. `outputs/exp1_proposed_deployments.csv`
2. `outputs/exp2_baseline_deployments.csv`
3. `outputs/exp3_drift_correction.csv`
4. `outputs/exp4_rollback.csv`
5. `outputs/exp5_chaos_resilience.csv`
6. `outputs/exp6_hpa_scaling.csv`
7. `outputs/paper_statistics.txt`
8. `outputs/stage4_run.log`

Then say: **"Here is my real experimental data. Rewrite the paper."**

Claude will:
- Replace all fabricated statistics with your real measured values
- Fix the degrees of freedom in Welch t-test (was suspicious at df=3.92)
- Add the chaos resilience section as a novel fifth experimental dimension
- Completely rewrite Threats to Validity (remove the synthetic data admission)
- Update all tables with real numbers
- Ensure statistical language is precise and reviewer-proof

---

## CLEANUP AFTER EXPERIMENTS

```bash
# Delete production workloads
kubectl delete namespace production

# Delete Argo CD applications
kubectl delete -f k8s-manifests/argocd/applications.yaml

# OPTIONAL: Delete Argo CD itself
kubectl delete namespace argocd

# OPTIONAL: Terminate EKS cluster (if done)
eksctl delete cluster kastro-cluster --region ap-south-1
```

---

## TROUBLESHOOTING

### "curl: UNREACHABLE" on health endpoints
```bash
# Check security group rule exists
aws ec2 describe-security-group-rules \
    --filters "Name=group-id,Values=sg-03d98966b4e46b121" \
    --query "SecurityGroupRules[?FromPort<=\`31096\`&&ToPort>=\`31096\`]" \
    --region ap-south-1

# If missing, add it:
aws ec2 authorize-security-group-ingress \
    --group-id sg-03d98966b4e46b121 \
    --protocol tcp --port 30000-32767 \
    --cidr 0.0.0.0/0 --region ap-south-1
```

### Pods not starting
```bash
kubectl describe pod -n production | tail -30
kubectl logs -n production -l app=user-service
```

### Docker push fails
```bash
docker logout && docker login -u kastrov
```

### Argo CD application stuck OutOfSync
```bash
# Force sync
kubectl patch application user-service -n argocd \
    --type merge -p '{"operation": {"sync": {}}}'
```

### Stage 4 fails at pre-flight check
The two health curl checks must return 200 before experiments start.
Check: pods running, NodePort open, using correct node IP (13.233.100.26).
