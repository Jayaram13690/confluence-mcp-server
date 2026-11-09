project_id   = "gbg-wxcc"
region       = "us-central1"
cluster_name = "neuroaiengg-gke-cluster"
clustertype  = "gke"
charts = {
  neuroaimcp = {
    chart            = "../../helm-chart/neuroai-mcp"
    deploymentname   = "neuroaimcpdeploy"
    chartversion     = "1.0.0"
    chartrepository  = ""
    values-files     = ["../../values-files/values-demo.yaml"]
    namespace        = "neuroai-mcp"
    clustertype      = "gke"
    create_namespace = true
    timeout          = 120
  }
}