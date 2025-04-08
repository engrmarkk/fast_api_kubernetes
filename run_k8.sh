#!/bin/bash

kubectl apply -f ./k8/api/ -f ./k8/redis/ -f ./k8/celery/ -f ./k8/ -n wallet-namespace

echo "Waiting for pods to be ready"
# sleep for 10 seconds
sleep 10
kubectl get pods -n wallet-namespace

echo "Waiting for services to be ready"
# sleep for 10 seconds
sleep 10
kubectl get svc -n wallet-namespace
