#!/bin/bash
# ============================================================
# STAGE 1: ENVIRONMENT SETUP
# - Installs pip3 and Python dependencies
# - Opens NodePort range on worker node security group
# - Verifies cluster connectivity
# ============================================================
set -e

SG_ID="sg-0f2079a4ca699a4a8"
REGION="ap-south-1"
NODE_IP_1="143.204.144.182"
NODE_IP_2="13.234.217.134"

echo ""
echo "============================================================"
echo "  STAGE 1 STARTED: Environment Setup"
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

# ── pip3 and dependencies ─────────────────────────────────────
echo ""
echo "[1/4] Installing pip3 and Python dependencies..."
apt-get install -y python3-pip python3-venv > /dev/null 2>&1 || true
pip3 install requests --break-system-packages -q
echo "      OK: pip3 and requests installed"

# ── Open NodePort range on worker security group ──────────────
echo ""
echo "[2/4] Opening NodePort range (30000-32767) on security group $SG_ID..."
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 30000-32767 \
    --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null && echo "      OK: Port range opened" \
    || echo "      INFO: Rule already exists (that is fine)"

# Also open port 80 just in case
aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region "$REGION" 2>/dev/null && echo "      OK: Port 80 opened" \
    || echo "      INFO: Port 80 rule already exists"

# ── Verify kubectl ────────────────────────────────────────────
echo ""
echo "[3/4] Verifying cluster access..."
kubectl get nodes -o wide
echo "      OK: Cluster accessible"

# ── Verify Argo CD ───────────────────────────────────────────
echo ""
echo "[4/4] Verifying Argo CD is running..."
ARGOCD_PODS=$(kubectl get pods -n argocd --no-headers | grep Running | wc -l)
if [ "$ARGOCD_PODS" -ge 5 ]; then
    echo "      OK: Argo CD running ($ARGOCD_PODS pods)"
else
    echo "      WARNING: Only $ARGOCD_PODS Argo CD pods running. Expected at least 5."
    kubectl get pods -n argocd
fi

# ── Save node info ────────────────────────────────────────────
mkdir -p outputs
cat > outputs/env_info.txt <<EOF
NODE_IP_1=$NODE_IP_1
NODE_IP_2=$NODE_IP_2
USER_HEALTH=http://$NODE_IP_1:31096/health
PRODUCT_HEALTH=http://$NODE_IP_1:31471/health
USER_URL=http://$NODE_IP_1:31096/api/users
PRODUCT_URL=http://$NODE_IP_1:31471/api/products
SG_ID=$SG_ID
REGION=$REGION
CLUSTER=kastro-cluster
DOCKERHUB_USER=kastrov
EOF
echo ""
echo "      OK: Environment info saved to outputs/env_info.txt"

echo ""
echo "============================================================"
echo "  STAGE 1 COMPLETE"
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "  NEXT: Run ./stage2_build_push.sh"
echo "============================================================"
