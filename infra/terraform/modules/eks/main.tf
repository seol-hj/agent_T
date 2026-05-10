# ============================================================================
# module: eks
# 책임: EKS 클러스터 + Managed Node Group + OIDC provider.
# 활성화 단계: 5
#
# 설계:
#   - Cluster: private-app subnet에 배치
#   - Endpoint: public/private 접근 변수화 (dev: public, prod: private 권장)
#   - Node Group: managed node group (일반 워크로드 + SUMO 컴퓨팅용)
#   - IRSA: OIDC provider 자동 생성 → ServiceAccount ↔ IAM Role 연결
#   - Add-ons: vpc-cni, coredns, kube-proxy, eks-pod-identity-agent
# ============================================================================

locals {
  base_tags = var.tags

  cluster_name = "${var.project_name}-${var.env}-eks"
}

# ==== IAM Role for EKS Cluster ===============================================
# EKS 클러스터가 AWS API를 호출하기 위한 IAM Role (컨트롤 플레인).
resource "aws_iam_role" "cluster" {
  name = "${local.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(local.base_tags, {
    Name = "${local.cluster_name}-cluster-role"
  })
}

resource "aws_iam_role_policy_attachment" "cluster_amazon_eks_cluster_policy" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_role_policy_attachment" "cluster_amazon_eks_vpc_resource_controller" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
}

# ==== EKS Cluster Security Group ============================================
# EKS 클러스터용 security group (컨트롤 플레인 ↔ 노드 통신).
resource "aws_security_group" "cluster" {
  name        = "${local.cluster_name}-cluster-sg"
  description = "Security group for EKS cluster control plane"
  vpc_id      = var.vpc_id

  tags = merge(local.base_tags, {
    Name = "${local.cluster_name}-cluster-sg"
  })
}

# 노드 → 컨트롤 플레인 (HTTPS)
resource "aws_vpc_security_group_ingress_rule" "cluster_from_nodes" {
  security_group_id            = aws_security_group.cluster.id
  referenced_security_group_id = aws_security_group.node.id
  from_port                    = 443
  to_port                      = 443
  ip_protocol                  = "tcp"
  description                  = "Allow nodes to communicate with cluster API"
}

# 컨트롤 플레인 → 노드 (kubelet, pod metrics)
resource "aws_vpc_security_group_egress_rule" "cluster_to_nodes" {
  security_group_id            = aws_security_group.cluster.id
  referenced_security_group_id = aws_security_group.node.id
  from_port                    = 1025
  to_port                      = 65535
  ip_protocol                  = "tcp"
  description                  = "Allow cluster to communicate with nodes"
}

# ==== Node Security Group ===================================================
resource "aws_security_group" "node" {
  name        = "${local.cluster_name}-node-sg"
  description = "Security group for EKS worker nodes"
  vpc_id      = var.vpc_id

  tags = merge(local.base_tags, {
    Name                                        = "${local.cluster_name}-node-sg"
    "kubernetes.io/cluster/${local.cluster_name}" = "owned"
  })
}

# 노드 간 통신 (모든 프로토콜)
resource "aws_vpc_security_group_ingress_rule" "node_to_node" {
  security_group_id            = aws_security_group.node.id
  referenced_security_group_id = aws_security_group.node.id
  ip_protocol                  = "-1"
  description                  = "Allow nodes to communicate with each other"
}

# 컨트롤 플레인 → 노드
resource "aws_vpc_security_group_ingress_rule" "node_from_cluster" {
  security_group_id            = aws_security_group.node.id
  referenced_security_group_id = aws_security_group.cluster.id
  from_port                    = 1025
  to_port                      = 65535
  ip_protocol                  = "tcp"
  description                  = "Allow cluster control plane to communicate with nodes"
}

# 노드 → 외부 (모든 아웃바운드)
resource "aws_vpc_security_group_egress_rule" "node_all" {
  security_group_id = aws_security_group.node.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow nodes to communicate with internet (NAT or VPC Endpoints)"
}

# ==== EKS Cluster ===========================================================
resource "aws_eks_cluster" "this" {
  name     = local.cluster_name
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.private_app_subnet_ids
    endpoint_private_access = var.cluster_endpoint_private_access
    endpoint_public_access  = var.cluster_endpoint_public_access
    public_access_cidrs     = var.cluster_endpoint_public_access ? var.cluster_endpoint_public_access_cidrs : null
    security_group_ids      = [aws_security_group.cluster.id]
  }

  depends_on = [
    aws_iam_role_policy_attachment.cluster_amazon_eks_cluster_policy,
    aws_iam_role_policy_attachment.cluster_amazon_eks_vpc_resource_controller,
  ]

  tags = merge(local.base_tags, {
    Name = local.cluster_name
  })
}

# ==== OIDC Provider (IRSA) ==================================================
data "tls_certificate" "cluster" {
  count = var.enable_irsa ? 1 : 0

  url = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "cluster" {
  count = var.enable_irsa ? 1 : 0

  url             = aws_eks_cluster.this.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster[0].certificates[0].sha1_fingerprint]

  tags = merge(local.base_tags, {
    Name = "${local.cluster_name}-oidc-provider"
  })
}

# ==== IAM Role for Node Group ===============================================
resource "aws_iam_role" "node" {
  name = "${local.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(local.base_tags, {
    Name = "${local.cluster_name}-node-role"
  })
}

resource "aws_iam_role_policy_attachment" "node_amazon_eks_worker_node_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
}

resource "aws_iam_role_policy_attachment" "node_amazon_eks_cni_policy" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
}

resource "aws_iam_role_policy_attachment" "node_amazon_ec2_container_registry_read_only" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "node_amazon_ssm_managed_instance_core" {
  role       = aws_iam_role.node.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# ==== Managed Node Groups ===================================================
resource "aws_eks_node_group" "this" {
  for_each = var.node_groups

  cluster_name    = aws_eks_cluster.this.name
  node_group_name = "${local.cluster_name}-${each.key}"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_app_subnet_ids

  instance_types = each.value.instance_types
  capacity_type  = each.value.capacity_type
  disk_size      = each.value.disk_size

  scaling_config {
    desired_size = each.value.desired_size
    min_size     = each.value.min_size
    max_size     = each.value.max_size
  }

  update_config {
    max_unavailable = 1
  }

  labels = merge(
    each.value.labels,
    {
      "node-group" = each.key
    }
  )

  dynamic "taint" {
    for_each = each.value.taints
    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.node_amazon_eks_worker_node_policy,
    aws_iam_role_policy_attachment.node_amazon_eks_cni_policy,
    aws_iam_role_policy_attachment.node_amazon_ec2_container_registry_read_only,
  ]

  tags = merge(local.base_tags, {
    Name = "${local.cluster_name}-${each.key}"
  })
}

# ==== EKS Add-ons ===========================================================
resource "aws_eks_addon" "this" {
  for_each = var.cluster_addons

  cluster_name             = aws_eks_cluster.this.name
  addon_name               = each.key
  addon_version            = each.value.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [
    aws_eks_node_group.this
  ]

  tags = merge(local.base_tags, {
    Name = "${local.cluster_name}-addon-${each.key}"
  })
}
