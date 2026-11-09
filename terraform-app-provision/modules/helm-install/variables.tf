variable "kubeconfig" {
  description = "The Kubernetes configuration containing the host and certificate details"
  sensitive   = true
  type = object({
    host                   = string
    client_certificate     = optional(string)
    client_key             = optional(string)
    cluster_ca_certificate = string
    token                  = optional(string)
  })
}

variable "chart" {
  description = "Location of the helm chart"
  type        = string
}

variable "chartversion" {
  description = "Version of the chart to deploy. If not specified latest version will be used"
  type        = string
  default     = ""
}

variable "chartrepository" {
  description = "The repository for the chart"
  type        = string
  default     = ""
}

variable "values-files" {
  description = "List of Fully qualified values files"
  type        = list(any)
  default     = []
}

variable "namespace" {
  description = "Namespace for installation"
  type        = string
}

variable "deploymentname" {
  description = "Name of the deployment"
  type        = string
}

variable "clustertype" {
  description = "Type of the Kubernetes cluster"
  type        = string
  default     = ""

  validation {
    condition     = contains(["eks", "aks", "gke"], var.clustertype)
    error_message = "Valid values for clustertype are gke, eks and aks"
  }
}

variable "create_namespace" {
  type        = bool
  default     = false
  description = "Create namespace if it does not exist. By default the value is false"
}

variable "timeout" {
  type        = number
  default     = 120
  description = "The timeout for the helm install"
}