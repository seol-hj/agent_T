output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "vpc_cidr_block" {
  description = "VPC CIDR block."
  value       = aws_vpc.this.cidr_block
}

output "azs" {
  description = "이 VPC 가 펼쳐진 AZ 목록 (서브넷 인덱스와 1:1)."
  value       = var.azs
}

# ==== Subnet IDs ============================================================
output "public_subnet_ids" {
  description = "Public subnet IDs (ALB internet-facing / NAT 위치)."
  value       = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  description = "Private-app subnet IDs (EKS 노드, 서비스 — NAT 경유 외부 접근)."
  value       = aws_subnet.private_app[*].id
}

output "private_db_subnet_ids" {
  description = "Private-db subnet IDs (RDS / Redis / VPC Endpoint — intra-only)."
  value       = aws_subnet.private_db[*].id
}

output "database_subnet_ids" {
  description = "RDS aws_db_subnet_group.subnet_ids 에 그대로 사용 가능한 subnet 목록 (= private_db_subnet_ids)."
  value       = aws_subnet.private_db[*].id
}

# ==== Route Tables ==========================================================
output "public_route_table_id" {
  description = "Public route table ID."
  value       = aws_route_table.public.id
}

output "private_app_route_table_ids" {
  description = "Private-app route table IDs (AZ별)."
  value       = aws_route_table.private_app[*].id
}

output "private_db_route_table_ids" {
  description = "Private-db route table IDs (AZ별 — NAT 라우트 없음)."
  value       = aws_route_table.private_db[*].id
}

output "private_route_table_ids" {
  description = "VPC Endpoint(Gateway 타입, S3/DynamoDB) 가 attach 할 private route table 전체 (app + db)."
  value       = concat(aws_route_table.private_app[*].id, aws_route_table.private_db[*].id)
}

# ==== Gateways ==============================================================
output "internet_gateway_id" {
  description = "Internet Gateway ID."
  value       = aws_internet_gateway.this.id
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs (enable_nat_gateway=false 면 빈 list)."
  value       = aws_nat_gateway.this[*].id
}
