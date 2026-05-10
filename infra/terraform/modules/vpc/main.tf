# ============================================================================
# module: vpc
# 책임: VPC + 3-tier subnet (public / private-app / private-db)
#       + Internet Gateway + (선택) NAT Gateway + tier별 route table
# 활성화 단계: 3
# ============================================================================

locals {
  name_prefix = "${var.project_name}-${var.env}"

  # var.tags 는 env 단의 common_tags (project / env / managed_by 포함) 가 전달된다.
  # 모듈은 표준 태그를 재정의하지 않고, 리소스 고유 태그(Name / Tier / k8s role) 만 merge.
  base_tags = var.tags

  az_count = length(var.azs)

  # AZ 마지막 한 글자 (ap-northeast-2a → "a"). 리소스명 길이/가독성 위해.
  az_suffix = [for az in var.azs : substr(az, length(az) - 1, 1)]

  # CIDR 자동 도출 — 사용자가 명시 override 한 경우 그 값을 사용.
  public_cidrs = length(var.public_subnet_cidrs) > 0 ? var.public_subnet_cidrs : [
    for i in range(local.az_count) : cidrsubnet(var.vpc_cidr, 4, i)
  ]

  private_app_cidrs = length(var.private_app_subnet_cidrs) > 0 ? var.private_app_subnet_cidrs : [
    for i in range(local.az_count) : cidrsubnet(var.vpc_cidr, 4, i + 4)
  ]

  private_db_cidrs = length(var.private_db_subnet_cidrs) > 0 ? var.private_db_subnet_cidrs : [
    for i in range(local.az_count) : cidrsubnet(var.vpc_cidr, 4, i + 8)
  ]

  nat_gateway_count = var.enable_nat_gateway ? (var.single_nat_gateway ? 1 : local.az_count) : 0
}

# ==== VPC ===================================================================
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# ==== Internet Gateway ======================================================
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-igw"
  })
}

# ==== Subnets ===============================================================
resource "aws_subnet" "public" {
  count                   = local.az_count
  vpc_id                  = aws_vpc.this.id
  cidr_block              = local.public_cidrs[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.base_tags, {
    Name                     = "${local.name_prefix}-public-${local.az_suffix[count.index]}"
    Tier                     = "public"
    "kubernetes.io/role/elb" = "1"
  })
}

resource "aws_subnet" "private_app" {
  count             = local.az_count
  vpc_id            = aws_vpc.this.id
  cidr_block        = local.private_app_cidrs[count.index]
  availability_zone = var.azs[count.index]

  tags = merge(local.base_tags, {
    Name                              = "${local.name_prefix}-private-app-${local.az_suffix[count.index]}"
    Tier                              = "private-app"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

resource "aws_subnet" "private_db" {
  count             = local.az_count
  vpc_id            = aws_vpc.this.id
  cidr_block        = local.private_db_cidrs[count.index]
  availability_zone = var.azs[count.index]

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-private-db-${local.az_suffix[count.index]}"
    Tier = "private-db"
  })
}

# ==== NAT (선택) ============================================================
resource "aws_eip" "nat" {
  count  = local.nat_gateway_count
  domain = "vpc"

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-eip-nat-${count.index}"
  })

  depends_on = [aws_internet_gateway.this]
}

resource "aws_nat_gateway" "this" {
  count         = local.nat_gateway_count
  allocation_id = aws_eip.nat[count.index].id
  # single 모드: NAT 1개를 public[0] 에 배치 (count.index 는 항상 0)
  # multi  모드: AZ별 public 서브넷에 1:1 배치
  subnet_id = aws_subnet.public[count.index].id

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-nat-${var.single_nat_gateway ? "shared" : local.az_suffix[count.index]}"
  })

  depends_on = [aws_internet_gateway.this]
}

# ==== Route Tables ==========================================================
# Public — 1 개 공유. 모든 public subnet 이 attach.
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-rt-public"
    Tier = "public"
  })
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  count          = local.az_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private App — AZ 별로 1개. NAT 라우트가 AZ별로 다를 수 있어 분리.
resource "aws_route_table" "private_app" {
  count  = local.az_count
  vpc_id = aws_vpc.this.id

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-rt-private-app-${local.az_suffix[count.index]}"
    Tier = "private-app"
  })
}

# enable_nat_gateway=false 면 라우트가 없으므로 private-app 도 사실상 intra. 의도된 동작.
resource "aws_route" "private_app_nat" {
  count                  = var.enable_nat_gateway ? local.az_count : 0
  route_table_id         = aws_route_table.private_app[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[var.single_nat_gateway ? 0 : count.index].id
}

resource "aws_route_table_association" "private_app" {
  count          = local.az_count
  subnet_id      = aws_subnet.private_app[count.index].id
  route_table_id = aws_route_table.private_app[count.index].id
}

# Private DB — AZ 별로 1개. 0.0.0.0/0 라우트 없음 (intra-only).
# VPC Endpoint(Gateway 타입, S3/DynamoDB) 가 prefix-list 라우트를 추가할 대상.
resource "aws_route_table" "private_db" {
  count  = local.az_count
  vpc_id = aws_vpc.this.id

  tags = merge(local.base_tags, {
    Name = "${local.name_prefix}-rt-private-db-${local.az_suffix[count.index]}"
    Tier = "private-db"
  })
}

resource "aws_route_table_association" "private_db" {
  count          = local.az_count
  subnet_id      = aws_subnet.private_db[count.index].id
  route_table_id = aws_route_table.private_db[count.index].id
}
