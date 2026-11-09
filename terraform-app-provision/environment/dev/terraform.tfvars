project_id   = "gbg-wxcc"
region       = "us-east4"
cluster_name = "neuroaieng-gke-cluster-dev"
clustertype  = "gke"
charts = {
  neuroaimcp = {
    chart            = "../../helm-chart/neuroai-mcp"
    deploymentname   = "neuroai-confluence-mcpdeploy"
    chartversion     = "1.0.0"
    chartrepository  = ""
    values-files     = ["../../values-files/values-dev.yaml"]
    namespace        = "neuroai-mcp"
    clustertype      = "gke"
    create_namespace = true
    timeout          = 120
  }
}