provider "kubernetes" {
}

# Original helm provider with kubeconfig
provider "helm" {
  kubernetes = {
    host = local.kubeconfig.host

    client_certificate     = var.clustertype == "aks" ? base64decode(local.kubeconfig.client_certificate) : null
    client_key             = var.clustertype == "aks" ? base64decode(local.kubeconfig.client_key) : null
    cluster_ca_certificate = base64decode(local.kubeconfig.cluster_ca_certificate)
    token                  = var.clustertype != "aks" ? local.kubeconfig.token : null
  }
}

# This module block deploys Helm charts using the helm-install module.
# It iterates over the 'charts' variable, passing chart-specific parameters and provider configuration.
module "helm" {
  source   = "../../modules/helm-install"
  for_each = var.charts
  providers = {
    helm = helm
  }

  chart            = each.value.chart
  deploymentname   = each.value.deploymentname
  chartversion     = each.value.chartversion
  chartrepository  = each.value.chartrepository
  clustertype      = each.value.clustertype
  values-files     = each.value.values-files
  namespace        = each.value.namespace
  create_namespace = each.value.create_namespace
  kubeconfig       = local.kubeconfig
  timeout          = each.value.timeout
}
