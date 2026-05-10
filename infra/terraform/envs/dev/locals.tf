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

  # Policy ARNs (계산 가능한 형태)
  alb_controller_policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${local.name_prefix}-alb-controller-policy"
  bedrock_policy_arn        = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${local.name_prefix}-bedrock-invoke"

  # IRSA service accounts with policies attached
  service_accounts_with_policies = merge(
    var.service_accounts,
    {
      aws-load-balancer-controller = merge(
        var.service_accounts["aws-load-balancer-controller"],
        {
          policy_arns = [local.alb_controller_policy_arn]
        }
      )
      agent-service = merge(
        var.service_accounts["agent-service"],
        {
          policy_arns = [local.bedrock_policy_arn]
        }
      )
    }
  )
}
