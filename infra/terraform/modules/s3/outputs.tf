# ============================================================================
# 명시 출력 — 사용자 spec 의 4 종.
# ============================================================================
output "artifact_bucket_name" {
  description = "SUMO 입출력 산출물 버킷 이름."
  value       = aws_s3_bucket.this["artifact"].id
}

output "rag_source_bucket_name" {
  description = "RAG 문서 원본 버킷 이름."
  value       = aws_s3_bucket.this["rag_source"].id
}

output "reports_bucket_name" {
  description = "정책 리포트 (MD/PDF/HTML) 버킷 이름."
  value       = aws_s3_bucket.this["reports"].id
}

output "model_data_bucket_name" {
  description = "Fine-tuning / evaluation 데이터셋 버킷 이름."
  value       = aws_s3_bucket.this["model_data"].id
}

# ============================================================================
# 보조 출력 — 다른 모듈/IRSA 정책에서 일괄 참조 시 유용.
# ============================================================================
output "bucket_names" {
  description = "버킷 키 → 이름 map."
  value       = { for k, v in aws_s3_bucket.this : k => v.id }
}

output "bucket_arns" {
  description = "버킷 키 → ARN map."
  value       = { for k, v in aws_s3_bucket.this : k => v.arn }
}

output "artifact_bucket_arn" {
  description = "Artifact 버킷 ARN (IAM 정책 자원 지정용)."
  value       = aws_s3_bucket.this["artifact"].arn
}

output "rag_source_bucket_arn" {
  value = aws_s3_bucket.this["rag_source"].arn
}

output "reports_bucket_arn" {
  value = aws_s3_bucket.this["reports"].arn
}

output "model_data_bucket_arn" {
  value = aws_s3_bucket.this["model_data"].arn
}
