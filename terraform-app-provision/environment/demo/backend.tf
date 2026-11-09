# Details such as bucket and prefix will be passed through conf file
terraform {
  required_version = "~> 1.3"

  backend "gcs" {
    bucket = "neuroaiengg-demo-gke-terraform-state"
    prefix = "neuroaiengineering-mcp-demo"
  }
}