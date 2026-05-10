# ============================================================================
# module: ecr
# 책임: 서비스/실행 이미지별 ECR 리포지토리 + 라이프사이클 + 암호화 + 스캔.
# 활성화 단계: 4
#
# 레포 이름 패턴: <project>-<env>/<repo>
#   예) agent-t-dev/api-service, agent-t-prod/simulation-runner
#
# 태그 전략 (docs/ecr.md 참조):
#   - latest 금지
#   - sha-<short-sha> (CI 자동) + v<semver> (릴리즈)
# ============================================================================

locals {
  base_tags = var.tags

  repository_namespace = "${var.project_name}-${var.env}"

  # 라이프사이클 정책 (jsonencode) — 두 룰을 환경 공통으로 적용.
  # rule 1 : untagged 이미지 만료
  # rule 2 : tag_prefix_filters (default ["sha-"]) 매칭 태그 중 최근 N 개만 유지
  #          → "v" 시작 릴리즈 태그는 정리 대상이 아니어서 영구 보존됨
  lifecycle_rules = concat(
    [
      {
        rulePriority = 1
        description  = "Expire untagged images older than ${var.untagged_image_expiration_days} days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_expiration_days
        }
        action = { type = "expire" }
      },
    ],
    var.tagged_image_retention_count > 0 ? [
      {
        rulePriority = 2
        description  = "Keep last ${var.tagged_image_retention_count} images with tag prefixes ${join(",", var.tag_prefix_filters)}"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = var.tag_prefix_filters
          countType     = "imageCountMoreThan"
          countNumber   = var.tagged_image_retention_count
        }
        action = { type = "expire" }
      },
    ] : [],
  )

  lifecycle_policy = jsonencode({
    rules = local.lifecycle_rules
  })
}

# ==== Repositories ===========================================================
resource "aws_ecr_repository" "this" {
  for_each = toset(var.repositories)

  name                 = "${local.repository_namespace}/${each.key}"
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  encryption_configuration {
    encryption_type = var.kms_key_arn != "" ? "KMS" : "AES256"
    kms_key         = var.kms_key_arn != "" ? var.kms_key_arn : null
  }

  tags = merge(local.base_tags, {
    Name    = "${local.repository_namespace}/${each.key}"
    service = each.key
  })
}

# ==== Lifecycle policy =======================================================
resource "aws_ecr_lifecycle_policy" "this" {
  for_each = aws_ecr_repository.this

  repository = each.value.name
  policy     = local.lifecycle_policy
}
