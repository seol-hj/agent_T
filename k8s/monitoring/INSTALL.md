# Monitoring 설치 가이드

Prometheus + Grafana 설치 (Helm Chart)

---

## 전제 조건

- Kubernetes 클러스터 (EKS, Minikube, etc.)
- Helm 3.x
- kubectl

---

## 1. Prometheus Operator 설치

### Helm Repository 추가

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### kube-prometheus-stack 설치

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false
```

**포함 구성 요소**:
- Prometheus Operator
- Prometheus
- Alertmanager
- Grafana
- Node Exporter
- kube-state-metrics

### 설치 확인

```bash
kubectl get pods -n monitoring
```

---

## 2. Grafana 접근

### 비밀번호 확인

```bash
kubectl get secret -n monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

### 포트 포워딩

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

브라우저에서 http://localhost:3000 접근:
- Username: `admin`
- Password: (위에서 확인한 비밀번호)

---

## 3. Agent-T 서비스 메트릭 수집

### ServiceMonitor 생성

```bash
kubectl apply -f k8s/monitoring/agent-t-servicemonitor.yaml
```

### 서비스에 Label 추가

```yaml
# k8s/apps/*.yaml
metadata:
  labels:
    monitoring: "true"
```

### 메트릭 엔드포인트 추가 (향후)

FastAPI 서비스에 `/metrics` 엔드포인트 추가:

```python
from prometheus_client import make_asgi_app

app = FastAPI()
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

## 4. Grafana Dashboard Import

### Agent-T 대시보드

1. Grafana UI → Dashboard → Import
2. `docs/grafana-dashboards/agent-t-overview.json` 업로드

**포함 패널**:
- Pipeline 실행 횟수
- 단계별 Latency
- LLM 호출 횟수/Latency
- SUMO 실행 시간
- 에러율

---

## 5. CloudWatch Integration (EKS)

### CloudWatch Container Insights

```bash
# FluentBit 설치
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml
```

### Prometheus → CloudWatch

```bash
# AMP (Amazon Managed Prometheus) 사용
aws amp create-workspace --alias agent-t-prometheus
```

---

## 6. AlertManager 설정 (선택)

### Slack 알림 예시

```yaml
# values.yaml
alertmanager:
  config:
    global:
      slack_api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    route:
      receiver: 'slack-notifications'
    receivers:
      - name: 'slack-notifications'
        slack_configs:
          - channel: '#agent-t-alerts'
            text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

---

## 문제 해결

### Prometheus가 메트릭을 수집하지 못함

```bash
# ServiceMonitor 확인
kubectl get servicemonitors -n agent-t

# Prometheus 설정 확인
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# http://localhost:9090/targets
```

### Grafana 대시보드가 비어있음

- Data Source 확인: Configuration → Data Sources → Prometheus
- Query 테스트: Explore → Prometheus → 메트릭 선택

---

## 참고

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Operator](https://prometheus-operator.dev/)
