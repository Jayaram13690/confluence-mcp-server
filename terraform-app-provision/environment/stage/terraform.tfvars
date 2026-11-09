project_id   = "gbg-wxcc"
region       = "europe-west3"
cluster_name = "neuroaieng-gke-cluster-stage"
clustertype  = "gke"
charts = {
  neuroaimcp = {
    chart            = "../../helm-chart/neuroai-mcp"
    deploymentname   = "neuroaimcpdeploy"
    chartversion     = "1.0.0"
    chartrepository  = ""
    values-files     = ["../../values-files/values-stage.yaml"]
    namespace        = "neuroai-mcp"
    clustertype      = "gke"
    create_namespace = true
    timeout          = 120
  }
}