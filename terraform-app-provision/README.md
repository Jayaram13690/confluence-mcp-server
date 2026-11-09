# NeuroAI MCP GCP Deployment

## Overview

This directory provides Terraform modules and Helm charts for deploying the NeuroAI MCP application on Google Cloud Platform (GCP) using Google Kubernetes Engine (GKE).

---

## Directory Structure

```
terraform-app-provision/
  main.tf
  variables.tf
  modules/
    helm-install/
      main.tf
      output.tf
      providers.tf
      variables.tf
  helm-chart/
    neuroai-mcp/
      Chart.yaml
      README.md
      values.yaml
      docs/
        ...
      templates/
        ...
  values-files/
    values-dev.yaml
    ...
  examples/
    generate-certs.sh
    ...
alb-ssl/
  main.tf
  variables.tf
  backend.tf
  backend-dev.conf
  neuroai-mcp-helm-dev.aks.tfvars
  ssl/
    cert.crt
    private.key
```

---

## Prerequisites

- GCP project with billing enabled
- GKE cluster provisioned (not included in this repo)
- Google Cloud SDK (`gcloud`) installed and authenticated
- Terraform installed
- SSL certificate and private key files in `alb-ssl/ssl/`
- MCP Kubernetes Service annotated for NEG and BackendConfig

---

## Configuration

### 1. Prepare Environment

- Edit the appropriate `alb-ssl/alb-<env>.tfvars` and `backend-<env>.conf` for your environment.
- Generate a self-signed certificate if needed:
  ```sh
  cd alb-ssl/ssl
  ./generate-certs.sh
  ```

### 2. Initialize and Apply Terraform

- From the `alb-ssl` directory:
  ```sh
  terraform init -backend-config=backend-dev.conf
  terraform apply -var-file=alb-dev.tfvars
  ```
- This will provision the ALB, firewall, SSL, and health checks for the MCP app.

---

## Key Configuration Snippets

### MCP Service Manifest Example
```yaml
annotations:
  cloud.google.com/neg: '{"exposed_ports": {"8000":{}}}'
  cloud.google.com/backend-config: '{"default": "neuroai-mcp-backendconfig"}'
```

### Example alb-ssl/alb-dev.tfvars
```hcl
project              = "your-gcp-project"
region               = "your-region"
network              = "your-vpc"
subnetwork           = "your-subnet"
ssl_cert_name        = "your-ssl-cert"
url_map_name         = "your-url-map"
https_proxy_name     = "your-https-proxy"
forwarding_rule_name = "your-forwarding-rule"
gke_service_name     = "neuroai-mcp"
backend_port         = 8000
health_check_path    = "/mcp/health"
neg_a_name           = "auto-discovered-neg-a"
neg_a_zone           = "zone-a"
neg_b_name           = "auto-discovered-neg-b"
neg_b_zone           = "zone-b"
target_tags          = ["gke-node-pool-tag"]
```

---

## Troubleshooting

- Check ALB and backend health in GCP Console.
- Ensure firewall allows ALB and health check source ranges.
- Verify NEGs are healthy and have endpoints.
- Use `kubectl get svc,pods,endpoints` for GKE status.

---

## Security Considerations

- Store SSL keys securely.
- Restrict firewall rules to only required source ranges.
- Use private GKE clusters and VPCs.

---

## Contributing

- Test changes in a non-prod environment.
- Update documentation for new variables or resources.

---

## Support

- GCP Console > Network Services > Load Balancing
- GKE cluster logs and events
- Terraform logs and state
# NeuroAI MCP GCP Deployment

## Table of Contents
- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Deployment Instructions](#deployment-instructions)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [Support](#support)

---

## Overview

This repository provides Terraform modules and Helm charts for deploying the NeuroAI MCP application on Google Cloud Platform (GCP) using Google Kubernetes Engine (GKE). The deployment is split into two main parts:

- **terraform-app-provision**: Deploys the MCP app and supporting Kubernetes resources to GKE.
- **terraform-app-provision/alb-ssl**: Provisions the GCP Internal HTTPS Application Load Balancer (ALB), SSL, firewall, health checks, and backend service integration with GKE NEGs.

---

## Directory Structure

```
terraform-app-provision/
  main.tf
  variables.tf
  modules/
    helm-install/
      main.tf
      output.tf
      providers.tf
      variables.tf
  helm-chart/
    neuroai-mcp/
      Chart.yaml
      README.md
      values.yaml
      docs/
        example-all-configurations-withrdsca.yaml
        example-app-config.yaml
        example-ca-certs.yaml
        example-values-alb-ingress-with-oidc.yaml
        example-values-gcp.yaml
        example-values.yaml
      templates/
        neuroai-mcp-deployment.yaml
        neuroai-mcp-https-deployment.yaml
        neuroai-mcp-ingress.yaml
        neuroai-mcp-internal-loadbalancer-service.yaml
        neuroai-mcp-service.yaml
        neuroai-tls-secret-provider.yaml
        neuroai-tls-secret.yaml
  values-files/
    nginx-ingress-values.yaml
    values-dev.yaml
  examples/
    generate-certs.sh
    k8s-nginx-ingress-controller-helm.exampletfvars
    k8s-nginx-ingress-controller-values.yaml
alb-ssl/
  main.tf
  variables.tf
  backend.tf
  backend-dev.conf
  neuroai-mcp-helm-dev.aks.tfvars
  ssl/
    cert.crt
    private.key
```

---

## Prerequisites

- GCP project with billing enabled
- GKE cluster provisioned (not included in this repo)
- Google Cloud SDK (`gcloud`) installed and authenticated
- Terraform installed
- SSL certificate and private key files in `alb-ssl/ssl/`
- MCP Kubernetes Service annotated for NEG and BackendConfig

---

## Configuration

### terraform-app-provision

- Configure your Helm values and tfvars for the MCP app.
- Ensure the MCP Service manifest includes:
  ```yaml
  annotations:
    cloud.google.com/neg: '{"exposed_ports": {"8000":{}}}'
    cloud.google.com/backend-config: '{"default": "neuroai-mcp-backendconfig"}'
  ```

### alb-ssl

- Edit `alb-ssl/terraform.tfvars`:
  ```hcl
  project              = "your-gcp-project"
  region               = "your-region"
  network              = "your-vpc"
  subnetwork           = "your-subnet"
  ssl_cert_name        = "your-ssl-cert"
  url_map_name         = "your-url-map"
  https_proxy_name     = "your-https-proxy"
  forwarding_rule_name = "your-forwarding-rule"
  gke_service_name     = "neuroai-mcp"
  backend_port         = 8000
  health_check_path    = "/mcp/health"
  neg_a_name           = "auto-discovered-neg-a"
  neg_a_zone           = "zone-a"
  neg_b_name           = "auto-discovered-neg-b"
  neg_b_zone           = "zone-b"
  target_tags          = ["gke-node-pool-tag"]
  ```

---

## Deployment Instructions

1. **Deploy MCP App to GKE**
    - Use `terraform-app-provision` to deploy the MCP app and supporting resources.
    - Ensure the MCP Service and BackendConfig are created and NEG endpoints are healthy.

2. **Discover NEGs**
    ```sh
    gcloud compute network-endpoint-groups list --filter="name~'neuroai-mcp'" --format="table(name,zone,size)"
    ```
    Pick NEGs with non-zero size in the zones where your GKE pods are running.

3. **Update `alb-ssl/terraform.tfvars` with NEG names/zones**

4. **Deploy ALB/SSL module**
    ```sh
    cd alb-ssl
    terraform init -backend-config=backend-dev.conf
    terraform plan -var-file=neuroai-mcp-helm-dev.aks.tfvars
    terraform apply -var-file=neuroai-mcp-helm-dev.aks.tfvars
    ```

5. **Check ALB and backend health in GCP Console**

---

## Troubleshooting

- Check ALB and backend health in GCP Console.
- Ensure firewall allows ALB and health check source ranges.
- Verify NEGs are healthy and have endpoints.
- Use `kubectl get svc,pods,endpoints` for GKE status.

---

## Security Considerations

- Store SSL keys securely.
- Restrict firewall rules to only required source ranges.
- Use private GKE clusters and VPCs.

---

## Contributing

- Test changes in a non-prod environment.
- Update documentation for new variables or resources.

---

## Support

- GCP Console > Network Services > Load Balancing
- GKE cluster logs and events
- Terraform logs and state

## Overview
This directory contains Terraform scripts for deploying the NeuroAI Enterprise Portal application and supporting components to Kubernetes clusters using Helm charts. The deployment supports multiple cloud providers including Azure (AKS), AWS (EKS), and Google Cloud (GKE).

## Architecture
The Terraform configuration uses a modular approach to deploy Helm charts to Kubernetes clusters:
- **Main Module**: Orchestrates the deployment of multiple Helm charts
- **Helm Install Module**: Reusable module for installing Helm charts with various configurations
- **Multi-Cloud Support**: Supports AKS, EKS, and GKE clusters

## Components Deployed
The components are deployed in the following order to ensure proper dependencies:

1. **NGINX Ingress Controller**: Ingress controller for routing and SSL termination (deployed first)
2. **OAuth2 Proxy**: Authentication and authorization proxy for secure access (deployed second) 
3. **NeuroAI Enterprise Portal**: The main application containing the AI marketplace, components, and dashboard (deployed third)

## Traffic Flow and Authentication

### Network Architecture
The NeuroAI Enterprise Portal implements a layered security architecture with multiple ingress controllers:

```
Internet
    ↓
[Application Gateway / Load Balancer]  ← Cloud Provider Entry Point
    ↓
[NGINX Ingress Controller]             ← Internal routing and SSL termination
    ↓
[OAuth2 Proxy]                         ← Authentication layer
    ↓
[NeuroAI Enterprise Portal]            ← Application services
```

### Traffic Flow Details

#### 1. External Traffic Entry
- **Azure**: Traffic enters through Azure Application Gateway (AGIC) or Load Balancer
- **AWS**: Traffic enters through AWS Application Load Balancer
- **GCP**: Traffic enters through Google Cloud Load Balancer
- **SSL/TLS**: Terminated at the cloud provider level or NGINX ingress

#### 2. NGINX Ingress Layer
- **Purpose**: Internal routing, path-based routing, and additional SSL handling
- **Service Type**: ClusterIP (internal to cluster)
- **Exposed Via**: Cloud provider's ingress (AGIC/ALB/GLB)
- **Configuration**: Deployed via `nginx-ingress` chart with custom values

Example NGINX Ingress configuration:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: neuroai-nginx-ingress
  namespace: neuroai
  annotations:
    nginx.ingress.kubernetes.io/auth-url: "http://oauth2-proxy.oauth2-proxy.svc.cluster.local:4180/oauth2/auth"
    nginx.ingress.kubernetes.io/auth-signin: "https://$host/oauth2/start?rd=$escaped_request_uri"
    nginx.ingress.kubernetes.io/auth-response-headers: "x-auth-request-user, x-auth-request-email"
spec:
  ingressClassName: nginx
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: neuroai
            port:
              number: 7007
            port:
              number: 80
```

#### 3. Authentication Flow (OAuth2 Proxy)
The OAuth2 Proxy handles authentication before traffic reaches the NeuroAI application:

**Authentication Providers Supported:**
- **Azure AD / Microsoft Entra ID**: Enterprise SSO integration
- **AWS Cognito**: Identity and access management
- **Generic OIDC**: Any OpenID Connect provider
- **GitHub/GitLab**: Developer-focused authentication

**OAuth2 Flow:**
1. User accesses NeuroAI portal URL
2. NGINX ingress checks auth via OAuth2 proxy
3. If not authenticated:
   - Redirects to OAuth2 proxy (`/oauth2/start`)
   - OAuth2 proxy redirects to identity provider
   - User authenticates with identity provider
   - OAuth2 proxy receives callback and sets session cookie
4. Authenticated requests forwarded to NeuroAI application
### Detailed Traffic Flow via OAuth2 Proxy

For a detailed breakdown of the OAuth2 Proxy traffic flow—including request/response examples, endpoint descriptions, session management, and error handling—see [OAuth2 Proxy Traffic Flow Details](OAUTH2_TRAFFIC_FLOW.md).

**Summary:**  
The OAuth2 Proxy acts as an authentication layer between the NGINX ingress and the NeuroAI application. When a user accesses the portal, NGINX checks authentication via the OAuth2 Proxy. If the user is not authenticated, they are redirected to the identity provider (such as Azure AD) for login. Upon successful authentication, the OAuth2 Proxy sets a session cookie and forwards the request to the application with user identity headers. This ensures secure, SSO-enabled access to the NeuroAI portal.

#### 4. NeuroAI Application Layer
- **Backend Services**: Backstage-based portal with custom plugins
- **Database**: PostgreSQL for application data

### Security Features

#### Authentication & Authorization
- **SSO Integration**: Enterprise identity provider integration
- **Role-Based Access Control (RBAC)**: Kubernetes-native RBAC
- **Session Management**: Secure cookie-based sessions via OAuth2 proxy
- **Token Validation**: JWT/OIDC token validation

#### Network Security
- **Network Policies**: Kubernetes network policies for pod-to-pod communication
- **TLS Encryption**: End-to-end TLS encryption
- **Private Networking**: VNet/VPC integration for private cluster access
- **Firewall Rules**: Cloud provider firewall integration

#### Application Security
- **Content Security Policy (CSP)**: Browser-based security headers
- **CORS Configuration**: Cross-origin resource sharing controls
- **API Rate Limiting**: Request throttling and abuse prevention
- **Vulnerability Scanning**: Container and dependency scanning

### Monitoring Traffic
Monitor traffic flow using:
- **NGINX Ingress Metrics**: Request rates, response times, error rates
- **OAuth2 Proxy Logs**: Authentication events and failures
- **Application Metrics**: Custom NeuroAI metrics via Backstage
- **Cloud Provider Monitoring**: ALB/AGIC/GLB access logs

Example monitoring queries:
```bash
# Check NGINX ingress status
kubectl get ing -n neuroai

# View OAuth2 proxy logs
kubectl logs -n oauth2-proxy deployment/oauth-proxy

# Check NeuroAI application pods
kubectl get pods -n neuroai

# View ingress controller logs  
kubectl logs -n ingress-nginx deployment/ingress-nginx-ingress-nginx-controller
```

### Deployed Resource Names
After deployment, the following Kubernetes resources will be created:

#### NGINX Ingress Controller
- **Namespace**: `ingress-nginx`  
- **Deployment**: `ingress-nginx-ingress-nginx-controller`
- **Service**: `ingress-nginx-ingress-nginx-controller`
- **ServiceAccount**: `ingress-nginx-ingress-nginx`

#### OAuth2 Proxy  
- **Namespace**: `oauth2-proxy`
- **Deployment**: `oauth-proxy`
- **Service**: `oauth2-proxy`
- **ConfigMap**: `oauth2-proxy-config`

#### NeuroAI Enterprise Portal
- **Namespace**: `neuroai`
- **Deployment**: `neuroai` 
- **Service**: `neuroai`
- **Port**: `7007`

## Directory Structure
```
terraform-app-provision/
├── main.tf                         # Main Terraform configuration
├── variables.tf                    # Variable definitions
├── provider.tf                     # Provider configurations
├── backend.tf                      # Backend state configuration (generic)
├── backend-dev.conf                # Remote state config for dev
├── backend-stage1.conf             # Remote state config for stage1
├── backend-demo1.conf              # Remote state config for demo1
├── neuroai-helm-dev.aks.tfvars     # AKS variables for dev
├── neuroai-helm-stage1.aks.tfvars  # AKS variables for stage1
├── neuroai-helm-demo1.aks.tfvars   # AKS variables for demo1
├── modules/
│   └── helm-install/               # Reusable Helm installation module
├── helm-chart/
│   ├── neuroai/                    # NeuroAI Enterprise Portal Helm chart
│   └── oauth2proxy/                # OAuth2 Proxy Helm chart
├── values-files/
│   ├── values.yaml                 # Default values for deployments
│   ├── values-dev.yaml             # Values for dev environment
│   ├── values-stage1.yaml          # Values for stage1 environment
│   ├── values-demo1.yaml           # Values for demo1 environment
│   ├── app-config.yaml             # Application configuration
│   ├── all-configurations.yaml     # Additional configurations
│   ├── nginx-ingress-values.yaml   # NGINX ingress values
│   ├── oauth2proxy-values-dev.yaml     # OAuth2 proxy values for dev
│   ├── oauth2proxy-values-stage1.yaml  # OAuth2 proxy values for stage1
│   ├── oauth2proxy-values-demo1.yaml   # OAuth2 proxy values for demo1
└── examples/                        # Example configurations and scripts
  ├── neuroai-helm.aks.exampletfvars        # AKS deployment example
  ├── neuroai-helm.aws.exampletfvars        # EKS deployment example
  ├── neuroai-helm.gke.exampletfvars        # GKE deployment example
  ├── k8s-nginx-ingress-controller-helm.exampletfvars # NGINX ingress example
  └── provider.tf.*                   # Provider configurations for each cloud
```


## Prerequisites
Before deploying the application, ensure you have:

1. **Infrastructure Setup**: Kubernetes cluster should be provisioned using the scripts in `terraform-infra-provision`
2. **Kubernetes Access**: kubectl configured with access to the target cluster
3. **Terraform**: Version ~> 1.3 installed
4. **Helm**: Helm 3.x installed and configured
5. **Google Cloud SDK**: Installed and authenticated for GKE


## Configuration

### terraform-app-provision

- Configure your Helm values and tfvars for the MCP app.
- Ensure the MCP Service manifest includes:
  ```yaml
  annotations:
    cloud.google.com/neg: '{"exposed_ports": {"8000":{}}}'
    cloud.google.com/backend-config: '{"default": "neuroai-mcp-backendconfig"}'
  ```

### alb-ssl

- Edit `alb-ssl/terraform.tfvars`:
  ```hcl
  project              = "your-gcp-project"
  region               = "your-region"
  network              = "your-vpc"
  subnetwork           = "your-subnet"
  ssl_cert_name        = "your-ssl-cert"
  url_map_name         = "your-url-map"
  https_proxy_name     = "your-https-proxy"
  forwarding_rule_name = "your-forwarding-rule"
  gke_service_name     = "neuroai-mcp"
  backend_port         = 8000
  health_check_path    = "/mcp/health"
  neg_a_name           = "auto-discovered-neg-a"
  neg_a_zone           = "zone-a"
  neg_b_name           = "auto-discovered-neg-b"
  neg_b_zone           = "zone-b"
  target_tags          = ["gke-node-pool-tag"]
  ```

## Deployment Instructions

### 1. Prepare Configuration

Copy and customize the appropriate tfvars and backend config files for your environment:
```bash
# For dev
cp neuroai-helm-dev.aks.tfvars my-deployment.tfvars
cp backend-dev.conf my-backend.conf

# For stage1
cp neuroai-helm-stage1.aks.tfvars my-deployment.tfvars
cp backend-stage1.conf my-backend.conf

# For demo1
cp neuroai-helm-demo1.aks.tfvars my-deployment.tfvars
cp backend-demo1.conf my-backend.conf
```

### 2. Initialize Terraform (per environment)
```bash
# Example for dev environment
terraform init -backend-config=backend-dev.conf

# Example for stage environment
terraform init -backend-config=backend-stage.conf

# Example for demo environment
terraform init -backend-config=backend-demo.conf
```

### 3. Plan Deployment (per environment)
```bash
# Example for dev environment
terraform plan -var-file=neuroai-helm-dev.aks.tfvars

# Example for stage environment
terraform plan -var-file=neuroai-helm-stage1.aks.tfvars

# Example for demo environment
terraform plan -var-file=neuroai-helm-demo1.aks.tfvars
```

### 4. Apply Configuration (per environment)
```bash
# Example for dev environment
terraform apply -var-file=neuroai-helm-dev.aks.tfvars

# Example for stage environment
terraform apply -var-file=neuroai-helm-stage1.aks.tfvars

# Example for demo environment
terraform apply -var-file=neuroai-helm-demo1.aks.tfvars
```

### 5. Verify Deployment
```bash
# Check Helm releases
helm list -A

# Check pods
kubectl get pods -n neuroai

# Check services
kubectl get svc -n neuroai
```

## Example Deployments

### Complete Deployment Order
The components should be deployed in the following sequence:

### 1. NGINX Ingress Controller (Deploy First)
```hcl
charts = {
  nginx-ingress = {
    chart            = "ingress-nginx"
    deploymentname   = "ingress-nginx"
    chartversion     = "4.7.1"
    chartrepository  = "https://kubernetes.github.io/ingress-nginx"
    values-files     = ["values-files/nginx-ingress-values.yaml"]
    namespace        = "ingress-nginx"
    clustertype      = "aks"
    create_namespace = true
    timeout          = 300
  }
}
```

### 2. OAuth2 Proxy (Deploy Second)
```hcl
charts = {
  oauth2proxy = {
    chart            = "./helm-chart/oauth2proxy"
    deploymentname   = "oauth2proxydeploy"
    chartversion     = "1.0.0"
    chartrepository  = ""
    values-files     = ["values-files/oauth2proxy-values-<env>.yaml"]
    namespace        = "oauth2-proxy"
    clustertype      = "aks"
    create_namespace = true
    timeout          = 300
  }
}
```

Replace `<env>` with your target environment:
- `dev` for development
- `stage1` for stage1
- `demo1` for demo1

Example:
- For dev: `values-files/oauth2proxy-values-dev.yaml`
- For stage1: `values-files/oauth2proxy-values-stage1.yaml`
- For demo1: `values-files/oauth2proxy-values-demo1.yaml`

### 3. NeuroAI Enterprise Portal (Deploy Third)
For multi-environment deployments, use the same chart configuration and set the appropriate values file for each environment:

```hcl
charts = {
  neuroai = {
    chart            = "./helm-chart/neuroai"
    deploymentname   = "neuroaideploy"
    chartversion     = "1.0.0"
    chartrepository  = ""
    values-files     = ["values-files/values-<env>.yaml", "values-files/app-config.yaml", "values-files/all-configurations.yaml"]
    namespace        = "neuroai"
    clustertype      = "aks"
    create_namespace = true
    timeout          = 300
  }
}
```

Replace `<env>` with your target environment:
- `dev` for development
- `stage1` for stage1
- `demo1` for demo1

Example:
- For dev: `values-files/values-dev.yaml`
- For stage1: `values-files/values-stage1.yaml`
- For demo1: `values-files/values-demo1.yaml`

## State Management
Remote state backend configuration is managed using a basic `backend.tf` and separate `backend-<env>.conf` files for each environment.

**Process:**
1. `backend.tf` contains only the backend block without values:
  ```hcl
  terraform {
    backend "azurerm" {}
  }
  ```
2. For each environment, create a `backend-<env>.conf` file (e.g., `backend-dev.conf`, `backend-stage1.conf`, `backend-demo1.conf`) with the backend configuration:
  ```hcl
  resource_group_name  = "terraform-state-rg"
  storage_account_name = "terraformstatestorage"
  container_name       = "tfstate"
  key                  = "neuroai-app.<env>.tfstate"
  ```
3. Initialize Terraform for the desired environment:
  ```sh
  terraform init -backend-config=backend-dev.conf
  terraform init -backend-config=backend-stage1.conf
  terraform init -backend-config=backend-demo1.conf
  ```

This approach keeps state files isolated per environment and makes switching between environments simple and safe.

## Troubleshooting

### Common Issues
> **Note:** State and values files are per environment (e.g., dev, stage1, demo1). Issues such as failed deployments, state lock errors, or configuration mismatches are typically isolated to the specific environment. Always check the correct tfvars and backend config files for the environment you are troubleshooting.

1. **Helm Chart Not Found**
  - Verify chart path exists
  - Check chart repository URL if using external chart

2. **Namespace Creation Failed**
  - Ensure sufficient RBAC permissions
  - Check if namespace already exists

3. **Timeout During Deployment**
  - Increase timeout value
  - Check cluster resources and capacity
  - Verify image availability

4. **Authentication Failures**
  - Verify kubeconfig is correct
  - Check service principal permissions (Azure)
  - Ensure cluster access is configured

### Useful Commands
```bash
# Check Terraform state
terraform state list

# View specific resource
terraform state show module.helm["neuroai"].helm_release.charts

# Force refresh
terraform refresh -var-file=my-deployment.tfvars

# Destroy specific chart
terraform destroy -target=module.helm["chart-name"] -var-file=my-deployment.tfvars
```

## Security Considerations
- Store sensitive variables (client secrets, passwords) in secure vaults
- Use service principals with minimal required permissions
- Enable RBAC on Kubernetes clusters
- Configure network policies for pod-to-pod communication
- Use private container registries for application images

## Contributing
When adding new Helm charts or modifying configurations:
1. Test deployments in development environment first
2. Update documentation for any new variables or configurations
3. Add example tfvars files for new deployment scenarios
4. Ensure backward compatibility with existing deployments

## Support
For issues related to:
- **Infrastructure**: Check `terraform-infra-provision` directory
- **Application Configuration**: Review Helm chart values in `values-files/`
- **Deployment Issues**: Check Kubernetes cluster logs and Helm release status