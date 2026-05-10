# ============================================================================
# module: s3
# 책임: 4 종 버킷 생성 + 표준 보안 정책 (SSE / Public Block / Ownership /
#       Versioning / TLS-only) + 선택적 lifecycle.
# 활성화 단계: 4
#
# 버킷 키(local.buckets)는 underscore 표기. 실제 bucket 이름은
#   "<project>-<env>-<replace(key, _, -)>"  형태.
#   예) key="rag_source" → "agent-t-dev-rag-source"
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.env}"
  base_tags   = var.tags

  # 하드코딩된 4 종 버킷. 추가/제거가 필요하면 본 map 과 outputs.tf 를 함께 수정.
  buckets = {
    artifact = {
      description = "SUMO 시뮬레이션 입출력 (.net.xml / .rou.xml / raw / KPI)"
    }
    rag_source = {
      description = "RAG 문서 원본 (PDF / MD / 사용자 업로드)"
    }
    reports = {
      description = "정책 리포트 (Markdown / PDF / HTML + asset)"
    }
    model_data = {
      description = "Fine-tuning / evaluation 데이터셋"
    }
  }

  bucket_name = {
    for k, _ in local.buckets : k => "${local.name_prefix}-${replace(k, "_", "-")}"
  }

  # lifecycle_rules 중 enabled 인 것만 추출 (키는 local.buckets 에 존재해야 함)
  active_lifecycle = {
    for k, v in var.lifecycle_rules : k => v
    if try(v.enabled, false) && contains(keys(local.buckets), k)
  }
}

# ==== Buckets ===============================================================
resource "aws_s3_bucket" "this" {
  for_each = local.buckets

  bucket = local.bucket_name[each.key]

  tags = merge(local.base_tags, {
    Name    = local.bucket_name[each.key]
    purpose = each.key
  })
}

# ==== Object Ownership (BucketOwnerEnforced — ACL 비활성) ====================
resource "aws_s3_bucket_ownership_controls" "this" {
  for_each = local.buckets

  bucket = aws_s3_bucket.this[each.key].id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# ==== Public Access Block ====================================================
resource "aws_s3_bucket_public_access_block" "this" {
  for_each = local.buckets

  bucket = aws_s3_bucket.this[each.key].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ==== Versioning =============================================================
resource "aws_s3_bucket_versioning" "this" {
  for_each = local.buckets

  bucket = aws_s3_bucket.this[each.key].id

  versioning_configuration {
    status = "Enabled"
  }
}

# ==== Server-Side Encryption =================================================
# kms_key_arn 이 비어 있으면 SSE-S3 (AES256), 있으면 SSE-KMS.
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = local.buckets

  bucket = aws_s3_bucket.this[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null
    }
    # KMS 사용 시 bucket key 활성 → 요청당 KMS 호출 비용 절감
    bucket_key_enabled = var.kms_key_arn != ""
  }
}

# ==== TLS-only Bucket Policy =================================================
data "aws_iam_policy_document" "tls_only" {
  for_each = var.enforce_tls ? local.buckets : {}

  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    resources = [
      aws_s3_bucket.this[each.key].arn,
      "${aws_s3_bucket.this[each.key].arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "tls_only" {
  for_each = var.enforce_tls ? local.buckets : {}

  bucket = aws_s3_bucket.this[each.key].id
  policy = data.aws_iam_policy_document.tls_only[each.key].json

  # public access block 이 먼저 적용되어야 정책 거부 평가가 의도대로 동작
  depends_on = [aws_s3_bucket_public_access_block.this]
}

# ==== Lifecycle (선택) =======================================================
resource "aws_s3_bucket_lifecycle_configuration" "this" {
  for_each = local.active_lifecycle

  bucket = aws_s3_bucket.this[each.key].id

  rule {
    id     = "default"
    status = "Enabled"

    # 버킷 전체 객체 대상.
    filter {}

    dynamic "expiration" {
      for_each = each.value.expiration_days != null ? [1] : []
      content {
        days = each.value.expiration_days
      }
    }

    dynamic "noncurrent_version_expiration" {
      for_each = each.value.noncurrent_version_expiration_days != null ? [1] : []
      content {
        noncurrent_days = each.value.noncurrent_version_expiration_days
      }
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = each.value.abort_incomplete_multipart_days
    }
  }

  # versioning 이 먼저 활성화되어야 noncurrent_version_expiration 이 의미를 가진다.
  depends_on = [aws_s3_bucket_versioning.this]
}
