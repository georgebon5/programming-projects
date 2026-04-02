# Sealed Secrets Setup Guide

## Overview
Sealed Secrets encrypts Kubernetes secrets so they can be safely stored in Git.
Only the sealed-secrets controller (running in the cluster) can decrypt them.
The plaintext `secret.yml` in this directory is a **template only** — it contains
placeholder values and is safe to commit. Real secrets must be sealed before
being committed.

## Prerequisites
- `kubeseal` CLI installed locally
- Sealed Secrets controller installed in the cluster (see Installation below)
- `kubectl` configured to point at the target cluster

---

## Installation

### 1. Install the controller (one-time per cluster)
```bash
# Using Helm (recommended)
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system \
  --set fullnameOverride=sealed-secrets-controller

# Or using kubectl (direct manifest)
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.1/controller.yaml
```

Verify the controller is running:
```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=sealed-secrets
```

### 2. Install kubeseal CLI
```bash
# macOS
brew install kubeseal

# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.1/kubeseal-0.26.1-linux-amd64.tar.gz
tar -xvzf kubeseal-0.26.1-linux-amd64.tar.gz
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

Verify:
```bash
kubeseal --version
```

### 3. Fetch the cluster's public key
```bash
kubeseal --fetch-cert \
  --controller-name=sealed-secrets-controller \
  --controller-namespace=kube-system \
  > pub-cert.pem
```

Store `pub-cert.pem` locally (it is safe to commit — it is a public key).

---

## Usage

### Seal a secret

1. Copy the template outside the repo and fill in real values:
```bash
cp k8s/secret.yml /tmp/my-secret.yml
# Edit /tmp/my-secret.yml with real values
```

2. Seal it using the cluster's public key:
```bash
kubeseal --format yaml --cert pub-cert.pem \
  < /tmp/my-secret.yml \
  > k8s/sealed-secret.yml
```

3. Apply the sealed secret to the cluster:
```bash
kubectl apply -f k8s/sealed-secret.yml
```

4. Delete the plaintext copy immediately:
```bash
rm /tmp/my-secret.yml
```

5. Commit `sealed-secret.yml` to Git — it is safe because it is encrypted.

### Update a single secret value
```bash
echo -n "new-value" | kubeseal --raw \
  --name rag-secrets \
  --namespace rag-system \
  --cert pub-cert.pem
# Replace the corresponding encrypted value in k8s/sealed-secret.yml
```

### Rotate secrets
1. Copy `k8s/secret.yml` outside the repo and set new values
2. Re-seal:
```bash
kubeseal --format yaml --cert pub-cert.pem \
  < /tmp/my-secret.yml \
  > k8s/sealed-secret.yml
```
3. Apply the updated sealed secret:
```bash
kubectl apply -f k8s/sealed-secret.yml
```
4. Restart deployments to pick up the new values:
```bash
kubectl rollout restart deployment/rag-api deployment/celery-worker -n rag-system
```

---

## Important Notes

| File | Contains | Safe to commit? |
|---|---|---|
| `k8s/secret.yml` | Placeholder values only (template) | Yes |
| `k8s/sealed-secret.yml` | Encrypted values (kubeseal output) | Yes |
| `/tmp/my-secret.yml` | Real plaintext values | **Never** |
| `pub-cert.pem` | Controller public key | Yes |
| `master-key-backup.yml` | Controller private key (backup) | **Never** |

- SealedSecrets are **bound to the cluster and namespace** — a sealed secret for
  `rag-system` on cluster A cannot be decrypted on cluster B.
- If you lose the controller's private key, **all sealed secrets become
  unrecoverable**. Back up the key immediately after installation:
```bash
kubectl get secret -n kube-system \
  -l sealedsecrets.bitnami.com/sealed-secrets-key \
  -o yaml > master-key-backup.yml
```
  Store this backup in a secure location such as a password manager or secrets
  vault — **not in Git**.

---

## CI/CD Integration

In your CD pipeline, apply the sealed secret before the application manifests:

```bash
# Apply infrastructure / config first
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/sealed-secret.yml   # controller decrypts → Secret
kubectl apply -f k8s/configmap.yml

# Then apply workloads
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/redis.yml
kubectl apply -f k8s/api-deployment.yml
kubectl apply -f k8s/worker-deployment.yml
kubectl apply -f k8s/ingress.yml
```

The sealed-secrets controller will automatically decrypt `sealed-secret.yml` and
create the `rag-secrets` Secret in the `rag-system` namespace. Pods that
reference that Secret will start normally once it exists.

---

## Troubleshooting

**SealedSecret stays in `Pending` / Secret not created**
```bash
# Check controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=sealed-secrets

# Check events on the SealedSecret
kubectl describe sealedsecret rag-secrets -n rag-system
```

**`kubeseal: cannot fetch certificate` error**
- Ensure `kubectl` context points at the correct cluster
- Ensure the controller pod is running in `kube-system`

**Sealed secret decrypted on wrong cluster**
- SealedSecrets are cluster-scoped by default. Re-seal using the target
  cluster's public key (`--fetch-cert` on the correct cluster).
