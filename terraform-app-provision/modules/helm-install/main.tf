resource "helm_release" "deployment" {
  name             = var.deploymentname
  chart            = var.chart
  version          = var.chartversion != "" ? var.chartversion : null
  repository       = var.chartrepository != "" ? var.chartrepository : null
  namespace        = var.namespace
  values           = [for valuefile in var.values-files : file(valuefile)]
  create_namespace = var.create_namespace
  timeout          = var.timeout
}