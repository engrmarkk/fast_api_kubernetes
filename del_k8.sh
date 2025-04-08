#!/bin/bash

kubectl delete all --all -n wallet-namespace  # Deletes pods, services, deployments, etc.
kubectl delete configmap,secret --all -n wallet-namespace  # Delete configs and secrets
