#!/bin/bash
# ============================================================
# STAGE 3: DEPLOY TO KUBERNETES AND SETUP ARGO CD
# - Creates production namespace
# - Deploys user-service and product-service
# - Registers Argo CD applications
# - Verifies everything is healthy
# ============================================================
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="production"
NODE_IP="13.234.217.134"
ARGOCD_URL="a3b91fe804f58403ea8090b662886fe1-1066088423.ap-south-1.elb.amazonaws.com"

echo ""
echo "============================================================"
echo "  STAGE 3 STARTED: Kubernetes Deployment + Argo CD Setup"
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

# ── Create namespace ──────────────────────────────────────────
echo ""
echo "[1/7] Creating production namespace..."
kubectl apply -f "$REPO_ROOT/k8s-manifests/namespaces/production.yaml"
echo "      OK: Namespace ready"

# ── Deploy services ───────────────────────────────────────────
echo ""
echo "[2/7] Deploying user-service..."
kubectl apply -f "$REPO_ROOT/k8s-manifests/user-service/deployment.yaml"
echo "      OK: user-service manifest applied"

echo ""
echo "[3/7] Deploying product-service..."
kubectl apply -f "$REPO_ROOT/k8s-manifests/product-service/deployment.yaml"
echo "      OK: product-service manifest applied"

# ── Wait for pods ─────────────────────────────────────────────
echo ""
echo "[4/7] Waiting for pods to be Ready (up to 3 minutes)..."
kubectl wait --for=condition=available --timeout=180s \
    deployment/user-service -n "$NAMESPACE"
echo "      OK: user-service ready"
kubectl wait --for=condition=available --timeout=180s \
    deployment/product-service -n "$NAMESPACE"
echo "      OK: product-service ready"

# ── Verify NodePort reachability ──────────────────────────────
echo ""
echo "[5/7] Testing service health endpoints..."
sleep 5

for ATTEMPT in 1 2 3 4 5; do
    USER_RESP=$(curl -s --max-time 8 "http://${NODE_IP}:31096/health" || echo "FAIL")
    if echo "$USER_RESP" | grep -q "healthy"; then
        echo "      OK: user-service healthy: $USER_RESP"
        break
    else
        echo "      Attempt $ATTEMPT/5: user-service not ready yet, waiting 10s..."
        sleep 10
    fi
done

for ATTEMPT in 1 2 3 4 5; do
    PROD_RESP=$(curl -s --max-time 8 "http://${NODE_IP}:31471/health" || echo "FAIL")
    if echo "$PROD_RESP" | grep -q "healthy"; then
        echo "      OK: product-service healthy: $PROD_RESP"
        break
    else
        echo "      Attempt $ATTEMPT/5: product-service not ready yet, waiting 10s..."
        sleep 10
    fi
done

# ── Setup Argo CD ─────────────────────────────────────────────
echo ""
echo "[6/7] Setting up Argo CD applications..."
echo ""
echo "      IMPORTANT: You need to complete 3 manual steps first:"
echo ""
echo "      STEP A — Create a GitHub repo called 'gitops-repo' at:"
echo "               https://github.com/new"
echo "               Name: gitops-repo | Visibility: Public | Init with README"
echo ""
echo "      STEP B — Push k8s-manifests to that repo:"
echo "               cd $REPO_ROOT"
echo "               git init gitops-repo-local"
echo "               cp -r k8s-manifests gitops-repo-local/"
echo "               cd gitops-repo-local"
echo "               git init && git add . && git commit -m 'initial'"
echo "               git branch -M main"
echo "               git remote add origin https://github.com/KastroVKiran/gitops-repo.git"
echo "               git push -u origin main"
echo ""
echo "      STEP C — Get Argo CD admin password:"
ARGOCD_PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" | base64 -d 2>/dev/null || echo "NOT_FOUND")
echo "               Password: $ARGOCD_PASS"
echo "               URL: http://$ARGOCD_URL"
echo ""
read -p "      Press ENTER after completing Steps A, B, C above..."

echo "      Applying Argo CD application manifests..."
kubectl apply -f "$REPO_ROOT/k8s-manifests/argocd/applications.yaml"
echo "      OK: Argo CD applications registered"

sleep 10
echo ""
echo "[7/7] Verifying Argo CD applications..."
kubectl get applications -n argocd 2>/dev/null || echo "      INFO: argocd CLI needed to list apps"
kubectl get pods -n "$NAMESPACE"
kubectl get svc -n "$NAMESPACE"

echo ""
echo "      Cluster state:"
kubectl get nodes
echo ""
echo "      Production pods:"
kubectl get pods -n production -o wide

mkdir -p "$REPO_ROOT/outputs"
cat > "$REPO_ROOT/outputs/deployment_info.txt" <<EOF
DEPLOYMENT INFO
================
Namespace: production
Node IP (primary): $NODE_IP
User Service: http://$NODE_IP:31096
Product Service: http://$NODE_IP:31471
User Health: http://$NODE_IP:31096/health
Product Health: http://$NODE_IP:31471/health
Argo CD URL: http://$ARGOCD_URL
Argo CD Password: $ARGOCD_PASS
Deploy Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
EOF

echo ""
echo "============================================================"
echo "  STAGE 3 COMPLETE"
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "  NEXT: Run ./stage4_experiments.py"
echo "  Start it with: python3 scripts/stage4_experiments.py"
echo "============================================================"
