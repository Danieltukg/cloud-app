#!/bin/bash

set -e

NAMESPACE="production"

echo "applying k8s manifests..."

kubectl apply -f ../k8s/namespace.yml
kubectl apply -f ../k8s/postgres.yml
kubectl apply -f ../k8s/deployment.yml
kubectl apply -f ../k8s/service.yml
kubectl apply -f ../k8s/ingress.yml
kubectl apply -f ../k8s/hpa.yml

echo "waiting for postgres..."
kubectl rollout status deployment/postgres -n $NAMESPACE --timeout=120s

echo "waiting for app..."
kubectl rollout status deployment/app -n $NAMESPACE --timeout=120s

echo "done. pods:"
kubectl get pods -n $NAMESPACE
