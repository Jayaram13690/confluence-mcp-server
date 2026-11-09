output "status" {
  value = helm_release.deployment.status
}

output "chart_details" {
  value = "Chart: ${helm_release.deployment.metadata.chart}\nChart Version:${helm_release.deployment.metadata.version}\nNamespace: ${helm_release.deployment.metadata.namespace}\nDeployment Name: ${helm_release.deployment.metadata.name}\nDeployment Version: ${helm_release.deployment.metadata.revision}\nApplication Version:  ${helm_release.deployment.metadata.app_version}"
}