locals {
  name_prefix = "${var.project_name}-${var.env}"

  # 태그 키는 lowercase 로 통일 (project / env / managed_by).
  # 사용자 추가 태그는 var.tags 로 병합. 표준 키 충돌 시 사용자 값이 우선.
  common_tags = merge(
    {
      project    = var.project_name
      env        = var.env
      managed_by = "terraform"
    },
    var.tags,
  )
}
