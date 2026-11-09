# Deployment

- Edit your values file (e.g., `values-dev.yaml`) as needed for your environment.
- Deploy the chart using Helm (if not using Terraform):
	```sh
	helm upgrade --install neuroai-mcp . -f ../../values-files/values-dev.yaml
	```
- If using Terraform, the Helm chart will be deployed automatically as part of the infrastructure provisioning.

# NeuroAI MCP Charts Repo

Helm chart for NeuroAI MCP (Machine Comprehension Platform).  
This chart creates the required Kubernetes ConfigMaps, Service, Secrets, and Deployment files for NeuroAI MCP.  

## Prerequisites

- Kubernetes cluster (AKS recommended)
- Helm 3.x
- Access to container registry with the MCP image
- PostgreSQL database (provisioned separately)
- TLS certificates (self-signed or from a trusted CA)
- Nginx Ingress Controller (can be installed separately or as part of deployment)
