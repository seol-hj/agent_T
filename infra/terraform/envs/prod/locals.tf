locals {
  name_prefix = "${var.project_name}-${var.env}"

  # 태그 키는 lowercase 로 통일 (project / env / managed_by).
  common_tags = merge(
    {
      project    = var.project_name
      env        = var.env
      managed_by = "terraform"
    },
    var.tags,
  )
}
