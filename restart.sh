#!/usr/bin/env bash
set -e

echo "[1/5] Reset minikube"
minikube delete --all --purge
minikube start --driver=docker
minikube addons enable ingress


# kubectl set image deploy/auth auth=auth:v1 -n microservices
# kubectl set image deploy/gateway gateway=gateway:v1 -n microservices

echo "[2/5] Build images"
    sudo docker build -t gateway:v1 backend/gateway
    sudo docker build -t auth:v1 backend/auth

minikube image load gateway:v1 auth:v1

echo "[3/5] Apply manifests"
kubectl apply -f kuber/k8n/namespace.yaml \
  -f kuber/k8n/postgres-secret.yaml -f kuber/k8n/postgres.yaml \
  -f kuber/k8n/auth-config.yaml -f kuber/k8n/auth.yaml \
  -f kuber/k8n/gateway-config.yaml -f kuber/k8n/gateway.yaml \
  -f kuber/k8n/ingress.yaml

echo "[4/5] Wait for postgres (up to 40s)"
kubectl wait --for=condition=ready pod -l app=postgres -n microservices --timeout=40s

echo "[5/5] Run migrations job"
    kubectl apply -f kuber/k8n/alembic-job.yaml

# echo "[5/7] Restart deployments to pick new images"
# kubectl rollout restart deployment/auth deployment/gateway -n microservices

# echo "[6/7] Wait for availability"
# kubectl wait --for=condition=available deploy/auth deploy/gateway -n microservices --timeout=40s

echo "Ready. Port-forward"
# Это надо прописать ручками в терминале, чтобы получить доступ к сервисам из хоста
# Direct gateway (без /api префикса)"
# echo "    kubectl port-forward svc/gateway 8000:8000 -n microservices --address 0.0.0.0"

