#!/bin/bash

set -e

echo "installing k3s on master..."
curl -sfL https://get.k3s.io | sh -

echo "waiting for k3s to start..."
sleep 10

echo "getting node token..."
K3S_TOKEN=$(sudo cat /var/lib/rancher/k3s/server/node-token)
MASTER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "k3s master is up"
echo "run this on workers to join them:"
echo "curl -sfL https://get.k3s.io | K3S_URL=https://$MASTER_IP:6443 K3S_TOKEN=$K3S_TOKEN sh -"
