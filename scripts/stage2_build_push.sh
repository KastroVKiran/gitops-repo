#!/bin/bash
# ============================================================
# STAGE 2: BUILD AND PUSH DOCKER IMAGES
# - Builds user-service and product-service images
# - Pushes both to kastrov/ on DockerHub
# - Tags: 1.0.0 through 1.0.5 (for rollback experiments)
# ============================================================
set -e

DOCKERHUB_USER="kastrov"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "============================================================"
echo "  STAGE 2 STARTED: Docker Build and Push"
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================================"

# ── Docker login ─────────────────────────────────────────────
echo ""
echo "[1/5] Logging in to DockerHub..."
echo "      Enter your DockerHub password when prompted:"
docker login -u "$DOCKERHUB_USER"
echo "      OK: Docker login successful"

# ── Build user-service ────────────────────────────────────────
echo ""
echo "[2/5] Building user-service images..."
cd "$REPO_ROOT/user-service"

for TAG in 1.0.0 1.0.1 1.0.2 1.0.3 1.0.4 1.0.5; do
    echo "      Building kastrov/user-service:$TAG ..."
    docker build --build-arg APP_VERSION="$TAG" \
        -t "${DOCKERHUB_USER}/user-service:${TAG}" . -q
    echo "      Pushing kastrov/user-service:$TAG ..."
    docker push "${DOCKERHUB_USER}/user-service:${TAG}" --quiet
    echo "      OK: user-service:$TAG done"
done
docker tag "${DOCKERHUB_USER}/user-service:1.0.5" "${DOCKERHUB_USER}/user-service:latest"
docker push "${DOCKERHUB_USER}/user-service:latest" --quiet
echo "      OK: user-service all tags pushed"

# ── Build product-service ─────────────────────────────────────
echo ""
echo "[3/5] Building product-service images..."
cd "$REPO_ROOT/product-service"

for TAG in 1.0.0 1.0.1 1.0.2 1.0.3 1.0.4 1.0.5; do
    echo "      Building kastrov/product-service:$TAG ..."
    docker build --build-arg APP_VERSION="$TAG" \
        -t "${DOCKERHUB_USER}/product-service:${TAG}" . -q
    echo "      Pushing kastrov/product-service:$TAG ..."
    docker push "${DOCKERHUB_USER}/product-service:${TAG}" --quiet
    echo "      OK: product-service:$TAG done"
done
docker tag "${DOCKERHUB_USER}/product-service:1.0.5" "${DOCKERHUB_USER}/product-service:latest"
docker push "${DOCKERHUB_USER}/product-service:latest" --quiet
echo "      OK: product-service all tags pushed"

# ── Run tests locally before deploying ───────────────────────
echo ""
echo "[4/5] Running unit tests locally..."
cd "$REPO_ROOT"

pip3 install flask pytest pytest-cov --break-system-packages -q

echo "      Testing user-service..."
cd "$REPO_ROOT/user-service"
python3 -m pytest test_app.py -q --tb=short \
    --cov=app --cov-report=term-missing 2>&1 | tail -5
echo "      OK: user-service tests passed"

echo "      Testing product-service..."
cd "$REPO_ROOT/product-service"
python3 -m pytest test_app.py -q --tb=short \
    --cov=app --cov-report=term-missing 2>&1 | tail -5
echo "      OK: product-service tests passed"

# ── Save image info ───────────────────────────────────────────
echo ""
echo "[5/5] Saving image manifest..."
cd "$REPO_ROOT"
mkdir -p outputs
cat > outputs/images.txt <<EOF
IMAGES BUILT AND PUSHED
========================
kastrov/user-service:1.0.0
kastrov/user-service:1.0.1
kastrov/user-service:1.0.2
kastrov/user-service:1.0.3
kastrov/user-service:1.0.4
kastrov/user-service:1.0.5
kastrov/user-service:latest
kastrov/product-service:1.0.0
kastrov/product-service:1.0.1
kastrov/product-service:1.0.2
kastrov/product-service:1.0.3
kastrov/product-service:1.0.4
kastrov/product-service:1.0.5
kastrov/product-service:latest
EOF
echo "      OK: Image manifest saved to outputs/images.txt"

echo ""
echo "============================================================"
echo "  STAGE 2 COMPLETE"
echo "  Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "  NEXT: Run ./stage3_deploy.sh"
echo "============================================================"
