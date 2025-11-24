#!/usr/bin/env bash
set -euo pipefail

# Параметры
RESET_MINIKUBE=${RESET_MINIKUBE:-false}
IMG_TAG=${IMG_TAG:-v1}

if [[ "${RESET_MINIKUBE}" == "true" ]]; then
  echo "[1/6] Reset minikube (RESET_MINIKUBE=true)"
  minikube delete --all --purge
  minikube start --driver=docker
  minikube addons enable ingress
else
  echo "[1/6] Skip minikube reset (set RESET_MINIKUBE=true чтобы пересоздать кластер)"
fi


# kubectl set image deploy/auth auth=auth:v1 -n microservices
# kubectl set image deploy/gateway gateway=gateway:v1 -n microservices

echo "[2/6] Build images"
sudo docker build -t gateway:${IMG_TAG} backend/gateway
sudo docker build -t auth:${IMG_TAG} backend/auth

echo "[3/6] Load images into minikube"
minikube image load gateway:${IMG_TAG} auth:${IMG_TAG}

echo "[4/6] Apply manifests"
kubectl apply -f kuber/k8n/namespace.yaml \
  -f kuber/k8n/postgres-secret.yaml -f kuber/k8n/postgres.yaml \
  -f kuber/k8n/auth-config.yaml -f kuber/k8n/auth.yaml \
  -f kuber/k8n/gateway-config.yaml -f kuber/k8n/gateway.yaml \
  -f kuber/k8n/ingress.yaml

echo "[5/6] Restart deployments to pick new images"
kubectl set image deploy/auth auth=auth:${IMG_TAG} -n microservices
kubectl set image deploy/gateway gateway=gateway:${IMG_TAG} -n microservices
kubectl rollout restart deployment/auth deployment/gateway -n microservices


echo "[6/6] Run migrations job"
kubectl wait --for=condition=ready pod -l app=postgres -n microservices --timeout=40s
kubectl apply -f kuber/k8n/alembic-job.yaml

# echo "[5/7] Restart deployments to pick new images"
# kubectl rollout restart deployment/auth deployment/gateway -n microservices

# echo "[6/7] Wait for availability"
# kubectl wait --for=condition=available deploy/auth deploy/gateway -n microservices --timeout=40s

echo "Ready. Port-forward"
# Это надо прописать ручками в терминале, чтобы получить доступ к сервисам из хоста
# Direct gateway (без /api префикса)"
# echo "    kubectl port-forward svc/gateway 8000:8000 -n microservices --address 0.0.0.0"
