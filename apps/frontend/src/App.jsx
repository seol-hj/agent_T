import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [services, setServices] = useState({
    'api-service': { status: 'checking', url: '/api/health' },
    'agent-service': { status: 'checking', url: '/agent/health' },
    'simulation-service': { status: 'checking', url: '/simulation/health' },
    'analysis-service': { status: 'checking', url: '/analysis/health' },
    'report-service': { status: 'checking', url: '/reports/health' },
  })

  useEffect(() => {
    // 각 서비스 health check
    Object.entries(services).forEach(([name, config]) => {
      fetch(config.url)
        .then(res => res.json())
        .then(data => {
          setServices(prev => ({
            ...prev,
            [name]: { ...config, status: 'healthy', data }
          }))
        })
        .catch(err => {
          setServices(prev => ({
            ...prev,
            [name]: { ...config, status: 'unhealthy', error: err.message }
          }))
        })
    })
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#4ade80'
      case 'unhealthy': return '#f87171'
      default: return '#fbbf24'
    }
  }

  const getStatusEmoji = (status) => {
    switch (status) {
      case 'healthy': return '✅'
      case 'unhealthy': return '❌'
      default: return '⏳'
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🚗 Agent T</h1>
        <p>AI 기반 교통 시뮬레이션 지능화 플랫폼</p>
      </header>

      <main>
        <section className="status-section">
          <h2>서비스 상태</h2>
          <div className="services-grid">
            {Object.entries(services).map(([name, config]) => (
              <div key={name} className="service-card">
                <div className="service-header">
                  <span className="service-emoji">{getStatusEmoji(config.status)}</span>
                  <h3>{name}</h3>
                </div>
                <div className="service-status">
                  <span
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(config.status) }}
                  >
                    {config.status}
                  </span>
                </div>
                {config.data && (
                  <div className="service-info">
                    <p>Version: {config.data.version}</p>
                    <p>Service: {config.data.service}</p>
                  </div>
                )}
                {config.error && (
                  <div className="service-error">
                    <p>Error: {config.error}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="info-section">
          <h2>플랫폼 구성</h2>
          <div className="info-grid">
            <div className="info-card">
              <h3>📡 API Service</h3>
              <p>실험 관리 및 전체 워크플로우 조율</p>
            </div>
            <div className="info-card">
              <h3>🤖 Agent Service</h3>
              <p>LLM 기반 자연어 처리 및 에이전트</p>
            </div>
            <div className="info-card">
              <h3>🚦 Simulation Service</h3>
              <p>SUMO 기반 교통 시뮬레이션 실행</p>
            </div>
            <div className="info-card">
              <h3>📊 Analysis Service</h3>
              <p>시뮬레이션 결과 분석 및 KPI 추출</p>
            </div>
            <div className="info-card">
              <h3>📝 Report Service</h3>
              <p>정책 리포트 자동 생성</p>
            </div>
          </div>
        </section>

        <section className="architecture-section">
          <h2>아키텍처</h2>
          <div className="architecture-info">
            <ul>
              <li>☁️ AWS EKS (Kubernetes 1.30)</li>
              <li>🔄 GitOps with Argo CD</li>
              <li>🌐 AWS Load Balancer Controller (ALB)</li>
              <li>🗄️ RDS PostgreSQL + ElastiCache Redis</li>
              <li>📦 S3 + ECR</li>
              <li>🔐 IAM IRSA (ServiceAccount 기반 인증)</li>
            </ul>
          </div>
        </section>
      </main>

      <footer>
        <p>Agent T Platform v0.1.0 - Health Check Placeholder</p>
        <p>빌드 시간: {new Date().toLocaleString('ko-KR')}</p>
      </footer>
    </div>
  )
}

export default App
