variable "region" {
  description = "Region in case of AWS or GCP Cluster"
  default     = ""
  type        = string
}

variable "project_id" {
  description = "Project Id in case of GCP Cluster"
  default     = ""
  type        = string
}

variable "subscription_id" {
  description = "Azure Kubernetes Service Cluster subscription id"
  sensitive   = true
  default     = ""
}
variable "tenant_id" {
  description = "Azure Kubernetes Service Cluster tenant id"
  sensitive   = true
  default     = ""
}

variable "client_id" {
  description = "Azure Kubernetes Service Cluster client id"
  sensitive   = true
  default     = ""
}

variable "client_secret" {
  description = "Azure Kubernetes Service Cluster client secret"
  sensitive   = true
  default     = ""
}

variable "rg_name" {
  description = "The resource group name"
  type        = string
  default     = ""
}

variable "rg_location" {
  description = "The location to be used"
  type        = string
  default     = ""
}

variable "cluster_name" {
  description = "Cluster Name"
  type        = string
}

variable "clustertype" {
  description = "Type of the Kubernetes cluster (must be one of: aks, gke, eks)"
  type        = string
  validation {
    condition     = contains(["aks", "gke", "eks"], var.clustertype)
    error_message = "clustertype must be one of: aks, gke, eks."
  }
}

variable "charts" {
  description = "Map of Helm chart configurations to deploy multiple charts"
  type = map(object({
    chart            = string
    deploymentname   = string
    chartversion     = string
    chartrepository  = string
    values-files     = list(string)
    namespace        = string
    clustertype      = string
    create_namespace = bool
    timeout          = number
  }))
  default = {
    neuroaimcp = {
      chart            = "./helm-chart/neuroai-mcp"
      deploymentname   = "neuroaimcpdeploy"
      chartversion     = "1.0.0"
      chartrepository  = "https://charts.example.com/neuroaimcp"
      values-files     = ["values-neuroaimcp.yaml"]
      namespace        = "neuroai-mcp"
      clustertype      = "aks"
      create_namespace = true
      timeout          = 300
    }
  }
  validation {
    condition = alltrue([
      for c in values(var.charts) : contains(["eks", "aks", "gke"], c.clustertype)
    ])
    error_message = "Valid values for clustertype are gke, eks, and aks in all charts."
  }
}