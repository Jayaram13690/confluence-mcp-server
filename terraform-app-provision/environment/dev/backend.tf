# Details such as bucket and prefix will be passed through conf file
terraform {
  required_version = "~> 1.3"

  backend "gcs" {
    bucket = "neuroaiengineering-terraform-state-dev"
    prefix = "neuroaiengineering-confluence-mcp-dev"
  }
}