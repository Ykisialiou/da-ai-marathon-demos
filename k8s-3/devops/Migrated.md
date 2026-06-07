# Migrated
**Created at:** 2022-07-05
**Category:** DevOps / Security Architecture

---

## 1. Rotating SSL Certificates in HashiCorp Vault

Rotating the SSL/TLS certificate used by HashiCorp Vault is a critical task to ensure secure communication between clients (such as the External Secrets Operator) and the Vault server. 

### Step 1: Prepare the Certificate and Key Files
Ensure you have the following PEM-encoded files ready on the Vault server hosts (or available to the Vault container):
- `vault.crt`: The new public server certificate (including the full intermediate certificate chain).
- `vault.key`: The private key associated with the new certificate.
- `ca.crt`: The root CA certificate that signed the Vault certificate.

### Step 2: Place the Files and Check Ownership
Copy the files to the designated Vault configuration directory (typically `/etc/vault.d/vault-tls/`). Ensure the files have the correct ownership and permissions so the `vault` system user can read them:
```bash
sudo chown -R vault:vault /etc/vault.d/vault-tls/
sudo chmod 0600 /etc/vault.d/vault-tls/vault.key
sudo chmod 0644 /etc/vault.d/vault-tls/vault.crt /etc/vault.d/vault-tls/ca.crt
```

### Step 3: Update the Vault Configuration File
Ensure your Vault configuration file (e.g., `/etc/vault.d/vault.hcl`) points to the correct paths under the `listener "tcp"` block:
```hcl
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_cert_file = "/etc/vault.d/vault-tls/vault.crt"
  tls_key_file  = "/etc/vault.d/vault-tls/vault.key"
  tls_client_ca_file = "/etc/vault.d/vault-tls/ca.crt"
}
```

### Step 4: Apply the Certificate Change
Vault supports reloading its listener configuration without restarting the Vault process or sealing the storage. This prevents service disruption.
To reload the configuration, send a `SIGHUP` signal to the Vault process:

```bash
# Find the PID of the vault process
pid=$(pgrep vault)

# Send the SIGHUP signal to reload TLS certificates
sudo kill -HUP $pid
```

*Alternatively, if running on systemd:*
```bash
sudo systemctl reload vault
```

*Note:* If you are running Vault in a Kubernetes pod (e.g., using the official Helm chart), and the certificates are stored in a Kubernetes Secret, updating the Secret will automatically update the mounted files. You can reload the listener using:
```bash
kubectl exec -it vault-0 -- vault operator reload -tls
```

### Step 5: Verify the Certificate Rotation
Check that the listener is presenting the new certificate using `openssl`:
```bash
openssl s_client -connect vault.example.com:8200 -showcerts </dev/null
```
Verify the expiry dates and the issuer in the output to confirm rotation was successful.

---

## 2. Connecting Vault to Kubernetes via External Secrets Operator (ESO)

The External Secrets Operator (ESO) is a Kubernetes operator that integrates external secret management systems (like HashiCorp Vault) with Kubernetes. It reads information from Vault and automatically injects it as a native Kubernetes Secret.

### Step 1: Configure Kubernetes Authentication in Vault
Vault needs to trust the Kubernetes service account tokens to authenticate incoming requests from the External Secrets Operator.

1. **Enable the Kubernetes Authentication Method:**
   ```bash
   vault auth enable kubernetes
   ```

2. **Configure Vault with the Kubernetes Cluster Details:**
   Inside the Vault container or server:
   ```bash
   vault write auth/kubernetes/config \
       kubernetes_host="https://kubernetes.default.svc.cluster.local:443"
   ```

3. **Create a Vault Policy for Secrets Access:**
   Create a file named `eso-policy.hcl`:
   ```hcl
   path "secret/data/myapp/*" {
     capabilities = ["read"]
   }
   ```
   Write the policy to Vault:
   ```bash
   vault policy write eso-policy eso-policy.hcl
   ```

4. **Create a Vault Role mapping to the Kubernetes Service Account:**
   Map the policy to the service account used by the ESO in Kubernetes (usually `external-secrets` in the `external-secrets` namespace):
   ```bash
   vault write auth/kubernetes/role/eso-role \
       bound_service_account_names=external-secrets \
       bound_service_account_namespaces=external-secrets \
       policies=eso-policy \
       ttl=1h
   ```

### Step 2: Deploy and Configure ESO in Kubernetes

1. **Install ESO via Helm (if not already installed):**
   ```bash
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets \
       --namespace external-secrets \
       --create-namespace
   ```

2. **Create a SecretStore or ClusterSecretStore:**
   A `SecretStore` defines how to connect to Vault. To make Vault trust the new SSL certificate we rotated earlier, we must provide the Vault CA certificate inside the store configuration.

   Create a manifest named `vault-secret-store.yaml`:
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: SecretStore
   metadata:
     name: vault-backend
     namespace: default
   spec:
     provider:
       vault:
         server: "https://vault.example.com:8200"
         path: "secret"
         version: "v2"
         # Reference the CA certificate to trust Vault's TLS
         caBundle: "<BASE64_ENCODED_VAULT_CA_CRT>"
         auth:
           kubernetes:
             # Mount path for the Kubernetes auth method in Vault
             mountPath: "kubernetes"
             # Vault role configured to trust the service account
             role: "eso-role"
             # Local service account token to authenticate against Vault
             serviceAccountRef:
               name: "external-secrets"
   ```
   *Note: Place the base64-encoded content of `ca.crt` (the root/intermediate CA that signed Vault's certificate) inside the `caBundle` field. This ensures ESO can establish a secure, trusted TLS connection.*

   Apply the SecretStore:
   ```bash
   kubectl apply -f vault-secret-store.yaml
   ```

### Step 3: Retrieve Secrets via ExternalSecret
An `ExternalSecret` resource specifies which secret to fetch from Vault and how to map it to a Kubernetes Secret.

Create a manifest named `my-external-secret.yaml`:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-app-secret
  namespace: default
spec:
  refreshInterval: "1h" # How often to poll Vault for updates
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: k8s-app-secret # Name of the Kubernetes Secret to create
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_PASSWORD
      remoteRef:
        key: myapp/db
        property: password
```

Apply the ExternalSecret:
```bash
kubectl apply -f my-external-secret.yaml
```

### Step 4: Verification and Troubleshooting

1. **Verify the ExternalSecret Status:**
   ```bash
   kubectl get externalsecret my-app-secret
   ```
   The output should show `STATUS: SecretSynced`.

2. **Describe the Resource for Logs/Events:**
   ```bash
   kubectl describe externalsecret my-app-secret
   ```
   Look at the Events block to verify that the authentication and fetch operations succeeded.

3. **Verify the Generated Kubernetes Secret:**
   Check if the native Kubernetes Secret was created:
   ```bash
   kubectl get secret k8s-app-secret -o jsonpath='{.data.DATABASE_PASSWORD}' | base64 --decode
   ```
   This should return the decrypted password value stored in Vault.
