terraform {
  required_version = "~> 1.3"
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = "3.0.2"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.38.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "7.3.0"
    }
  }
}

provider "google" {
  region  = var.region
  project = var.project_id
}

data "google_container_cluster" "gke_cluster" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id
}

data "google_client_config" "current" {
}

locals {
  kubeconfig = {
    host : "https://${data.google_container_cluster.gke_cluster.endpoint}"
    cluster_ca_certificate : data.google_container_cluster.gke_cluster.master_auth[0].cluster_ca_certificate
    token : data.google_client_config.current.access_token
  }
}