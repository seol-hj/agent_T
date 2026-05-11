#!/bin/bash

# ============================================================================
# HTTPS + Route53 Domain Setup Script
# agent.seolphung.com → ALB (HTTPS only)
# ============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="agent.seolphung.com"
REGION="ap-northeast-2"
CERT_ARN="arn:aws:acm:ap-northeast-2:190484841865:certificate/03e82b5c-961c-43ea-93d5-027c5e9d1d6c"
ALB_DNS="k8s-default-frontend-5a9d8add64-2006189360.ap-northeast-2.elb.amazonaws.com"
ALB_HOSTED_ZONE_ID="Z3JE5OI70TWKCP"  # ap-northeast-2 ALB Hosted Zone ID

echo -e "${GREEN}=== HTTPS + Domain Setup ===${NC}"
echo ""
echo "Domain: ${DOMAIN}"
echo "Certificate: ${CERT_ARN}"
echo "ALB DNS: ${ALB_DNS}"
echo ""

# Step 1: Get Hosted Zone ID
echo -e "${YELLOW}Step 1: Getting Route53 Hosted Zone ID for seolphung.com...${NC}"
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name seolphung.com \
  --query 'HostedZones[0].Id' \
  --output text | cut -d'/' -f3)

if [ -z "$HOSTED_ZONE_ID" ]; then
  echo -e "${RED}❌ Hosted Zone not found for seolphung.com${NC}"
  echo "Please create a Hosted Zone first:"
  echo "  aws route53 create-hosted-zone --name seolphung.com --caller-reference $(date +%s)"
  exit 1
fi

echo -e "${GREEN}✅ Hosted Zone ID: ${HOSTED_ZONE_ID}${NC}"
echo ""

# Step 2: Add DNS validation record for ACM
echo -e "${YELLOW}Step 2: Getting ACM DNS validation record...${NC}"
VALIDATION_RECORD=$(aws acm describe-certificate \
  --certificate-arn "${CERT_ARN}" \
  --region "${REGION}" \
  --query 'Certificate.DomainValidationOptions[0].ResourceRecord' \
  --output json)

VALIDATION_NAME=$(echo $VALIDATION_RECORD | jq -r '.Name')
VALIDATION_VALUE=$(echo $VALIDATION_RECORD | jq -r '.Value')

echo "Validation CNAME:"
echo "  Name:  ${VALIDATION_NAME}"
echo "  Value: ${VALIDATION_VALUE}"
echo ""

echo -e "${YELLOW}Adding DNS validation record to Route53...${NC}"
aws route53 change-resource-record-sets \
  --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"${VALIDATION_NAME}\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{\"Value\": \"${VALIDATION_VALUE}\"}]
      }
    }]
  }" > /dev/null

echo -e "${GREEN}✅ DNS validation record added${NC}"
echo ""

# Step 3: Wait for certificate validation
echo -e "${YELLOW}Step 3: Waiting for ACM certificate validation...${NC}"
echo "This may take 5-10 minutes..."

aws acm wait certificate-validated \
  --certificate-arn "${CERT_ARN}" \
  --region "${REGION}" && \
  echo -e "${GREEN}✅ Certificate validated successfully${NC}" || \
  echo -e "${RED}❌ Certificate validation timeout (continuing anyway)${NC}"

echo ""

# Step 4: Add A record for domain → ALB
echo -e "${YELLOW}Step 4: Adding A record (ALIAS) for ${DOMAIN} → ALB...${NC}"
aws route53 change-resource-record-sets \
  --hosted-zone-id "${HOSTED_ZONE_ID}" \
  --change-batch "{
    \"Changes\": [{
      \"Action\": \"UPSERT\",
      \"ResourceRecordSet\": {
        \"Name\": \"${DOMAIN}\",
        \"Type\": \"A\",
        \"AliasTarget\": {
          \"HostedZoneId\": \"${ALB_HOSTED_ZONE_ID}\",
          \"DNSName\": \"dualstack.${ALB_DNS}\",
          \"EvaluateTargetHealth\": false
        }
      }
    }]
  }" > /dev/null

echo -e "${GREEN}✅ A record added${NC}"
echo ""

# Step 5: Display next steps
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Certificate ARN: ${CERT_ARN}"
echo ""
echo "Next steps:"
echo "  1. Update Helm values with certificate ARN"
echo "  2. Push to gitops/dev branch"
echo "  3. Argo CD will update ALB annotations"
echo "  4. Wait for DNS propagation (5-10 minutes)"
echo "  5. Test: curl -I https://${DOMAIN}"
echo ""
echo "Full instructions: docs/HTTPS-SETUP-GUIDE.md"
