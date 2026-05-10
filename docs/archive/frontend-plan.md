# 프론트엔드 UI 구성 계획

AI Agent T 플랫폼의 사용자 인터페이스 설계 및 구현 계획

---

## 📋 목차

1. [개요](#개요)
2. [기술 스택](#기술-스택)
3. [사용자 워크플로우](#사용자-워크플로우)
4. [페이지 구성](#페이지-구성)
5. [주요 컴포넌트](#주요-컴포넌트)
6. [백엔드 연동](#백엔드-연동)
7. [상태 관리](#상태-관리)
8. [배포 전략](#배포-전략)
9. [개발 로드맵](#개발-로드맵)

---

## 개요

### 목표

**일반 사용자도 코드 없이 교통 시뮬레이션을 실행하고 결과를 분석할 수 있는 직관적인 웹 인터페이스 제공**

### 핵심 가치

1. **접근성**: 자연어 입력으로 누구나 시뮬레이션 생성
2. **투명성**: AI가 생성한 시나리오를 확인하고 수정 가능
3. **실시간성**: 시뮬레이션 진행률 실시간 모니터링
4. **분석력**: 인터랙티브 차트로 KPI 이해
5. **비교 가능성**: 여러 실험 결과 비교 분석

---

## 기술 스택

### Core Framework

```yaml
Frontend:
  Framework: Next.js 14 (App Router)
  Language: TypeScript 5
  UI Library: React 18
  Styling: TailwindCSS 3 + shadcn/ui
  
State Management:
  Server State: TanStack Query (React Query) v5
  Client State: Zustand
  Form State: React Hook Form + Zod
  
Data Visualization:
  Charts: Recharts
  Maps: Leaflet (OpenStreetMap)
  Markdown: react-markdown
  
Realtime:
  Communication: Server-Sent Events (SSE)
  Fallback: Polling
  
Build & Deploy:
  Package Manager: pnpm
  Build Tool: Next.js built-in (Turbopack)
  Container: Docker
  Orchestration: Kubernetes (Helm)
```

### 선택 근거

| 기술 | 이유 |
|------|------|
| **Next.js 14** | SSR/SSG, API Routes, 최적화된 번들링, SEO |
| **TypeScript** | 타입 안전성, 백엔드 스키마와 일관성 |
| **TailwindCSS** | 빠른 UI 개발, 일관된 디자인 시스템 |
| **shadcn/ui** | 접근성 높은 컴포넌트 (Radix UI 기반) |
| **React Query** | 서버 상태 캐싱, 자동 재시도, Optimistic Update |
| **Recharts** | React 친화적, 반응형, 커스터마이징 용이 |
| **SSE** | 간단한 실시간 통신, WebSocket 대비 구현 용이 |

---

## 사용자 워크플로우

### 1. 실험 생성 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 자연어 입력                                                    │
│    "강남역 일대에서 교통량이 20% 증가했을 때 평균 통행 시간은?"   │
│    [텍스트 입력창]                                                │
│    [AI 시나리오 생성 버튼]                                        │
└─────────────────────────────────────────────────────────────────┘
                          ⬇ AI 분석 (5-10초)
┌─────────────────────────────────────────────────────────────────┐
│ 2. AI 시나리오 제안                                               │
│    ✓ 위치: 강남역 (경도/위도 자동 추출)                           │
│    ✓ 시나리오 타입: 수요 증가 (demand_change)                     │
│    ✓ 파라미터:                                                    │
│      - 기준 차량: 1,000대/시간                                    │
│      - 증가 비율: 20%                                             │
│      - 시뮬레이션 시간: 1시간                                      │
│    ✓ 분석 목표: 평균 통행 시간, 혼잡도                            │
│                                                                   │
│    [수정하기] [실행하기]                                           │
└─────────────────────────────────────────────────────────────────┘
                          ⬇ 사용자 확인
┌─────────────────────────────────────────────────────────────────┐
│ 3. 실행 확인                                                      │
│    예상 소요 시간: 2-3분                                          │
│    예상 비용: $0.05                                               │
│                                                                   │
│    [취소] [실행]                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 실행 모니터링 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│ 파이프라인 진행 상황                                              │
│                                                                   │
│ ✅ 1. 시나리오 생성       완료 (2초)                              │
│ ✅ 2. 도로망 구축         완료 (15초)                             │
│ ✅ 3. 교통 수요 생성      완료 (8초)                              │
│ 🔄 4. 시뮬레이션 실행     진행 중 (45%)                           │
│    └─ 차량 450/1000 완료                                         │
│ ⏳ 5. KPI 분석           대기 중                                  │
│ ⏳ 6. 리포트 생성         대기 중                                  │
│                                                                   │
│ [로그 보기] [취소]                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 3. 결과 분석 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│ 실험 결과: exp-20260508-001                                       │
│                                                                   │
│ [개요] [KPI 대시보드] [상세 데이터] [리포트]                       │
│                                                                   │
│ ┌───────────────────────────────────────────────────────────┐   │
│ │ 주요 지표 (KPI)                                            │   │
│ │                                                            │   │
│ │ 평균 통행 시간        350.2초  (+25% vs 기준선)            │   │
│ │ 평균 대기 시간        62.5초   (+45% vs 기준선)            │   │
│ │ 처리량                850대/시  (-15% vs 기준선)            │   │
│ │ 완료율                95.2%                                │   │
│ │ 혼잡도 지수           0.75     (보통 혼잡)                  │   │
│ │                                                            │   │
│ │ [차트: 시간대별 통행 시간]                                  │   │
│ │ [차트: 구간별 평균 속도]                                    │   │
│ └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│ [리포트 다운로드] [다른 실험과 비교] [시나리오 재실행]             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 페이지 구성

### 1. 대시보드 (/) - 홈

**목적**: 최근 실험 현황, 빠른 액션

```
┌───────────────────────────────────────────────────────────────┐
│ 🏠 AI Agent T                            [사용자] [설정] [로그아웃] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 대시보드                                                   │
│                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ 총 실험 수       │  │ 실행 중         │  │ 금월 비용    │ │
│  │ 156             │  │ 3               │  │ $12.50      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                               │
│  최근 실험                                  [+ 새 실험 생성]  │
│  ┌───────────────────────────────────────────────────────┐   │
│  │ exp-001  강남역 교통량 20% 증가  완료  2시간 전        │   │
│  │ exp-002  신호등 최적화         실행 중  진행률 60%     │   │
│  │ exp-003  차선 변경 영향 분석    완료  5시간 전        │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  빠른 시작 템플릿                                             │
│  [수요 증가 분석] [신호 최적화] [도로 확장 효과] [커스텀]    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 2. 새 실험 생성 (/experiments/new)

```
┌───────────────────────────────────────────────────────────────┐
│ 🧪 새 실험 생성                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  1️⃣ 자연어로 요구사항 입력                                     │
│  ┌───────────────────────────────────────────────────────┐   │
│  │ 교통 시뮬레이션 요구사항을 자유롭게 입력하세요           │   │
│  │                                                         │   │
│  │ 예: "강남역에서 신호 대기 시간을 10초 줄이면             │   │
│  │      전체 통행 시간이 얼마나 감소하나요?"               │   │
│  └───────────────────────────────────────────────────────┘   │
│  [AI 시나리오 생성] (Ctrl+Enter)                              │
│                                                               │
│  💡 예시:                                                     │
│  • 교통량이 30% 증가했을 때 혼잡도는?                         │
│  • 2차로를 3차로로 확장하면 처리량이 얼마나 증가?             │
│  • 좌회전 전용 신호를 추가하면 대기 시간은?                   │
│                                                               │
│  ────────────────────────────────────────────────────────     │
│                                                               │
│  2️⃣ AI 생성 시나리오 (자동 생성됨)                            │
│  ⏳ 시나리오를 생성 중입니다... (5-10초)                       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 3. 시나리오 확인 및 수정 (/experiments/new/review)

```
┌───────────────────────────────────────────────────────────────┐
│ 📝 시나리오 확인                           [뒤로] [수정] [실행]│
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  AI가 생성한 시나리오                                         │
│                                                               │
│  ┌─ 기본 정보 ──────────────────────────────────────────┐   │
│  │ 실험 ID: exp-20260508-001                             │   │
│  │ 위치: 강남역 일대 (127.028, 37.498)                   │   │
│  │ 시나리오 타입: 수요 증가 (demand_change)              │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ 시뮬레이션 설정 ────────────────────────────────────┐   │
│  │ 시간: 1시간 (07:00 - 08:00)                           │   │
│  │ Time Step: 1초                                        │   │
│  │ [상세 설정 펼치기]                                     │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ 기준선 (Baseline) ───────────────────────────────────┐   │
│  │ 차량 수: 1,000대/시간                                  │   │
│  │ 차종 비율: 승용차 80%, 버스 10%, 트럭 10%             │   │
│  │ [지도에서 보기]                                        │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ 변형 시나리오 (Variants) ────────────────────────────┐   │
│  │ ✓ Variant 1: 교통량 20% 증가                          │   │
│  │   - 차량 수: 1,200대/시간 (+20%)                      │   │
│  │   - 차종 비율: 동일                                    │   │
│  │                                                        │   │
│  │ [+ 변형 추가] [삭제]                                   │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─ 분석 목표 (KPIs) ────────────────────────────────────┐   │
│  │ ✓ 평균 통행 시간 (avg_travel_time)                    │   │
│  │ ✓ 평균 대기 시간 (avg_waiting_time)                   │   │
│  │ ✓ 처리량 (throughput)                                 │   │
│  │ ✓ 혼잡도 (congestion_index)                           │   │
│  │ [KPI 추가]                                             │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
│  예상 소요 시간: 2-3분                                        │
│  예상 비용: $0.05 (Bedrock API + SUMO 실행)                   │
│                                                               │
│  [취소] [다시 생성] [실행]                                     │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 4. 실행 모니터링 (/experiments/:id/running)

```
┌───────────────────────────────────────────────────────────────┐
│ 🔄 실험 실행 중: exp-20260508-001                             │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  파이프라인 진행 상황                    경과 시간: 01:25     │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ ✅ 1. 시나리오 생성 (Scenario Builder)    2초        │     │
│  │    └─ scenario-001.json 생성 완료                   │     │
│  │                                                      │     │
│  │ ✅ 2. 도로망 구축 (Network Builder)      15초        │     │
│  │    └─ network.net.xml (125 edges, 83 junctions)     │     │
│  │                                                      │     │
│  │ ✅ 3. 교통 수요 생성 (Demand Builder)    8초         │     │
│  │    └─ demand.rou.xml (1,200 vehicles)               │     │
│  │                                                      │     │
│  │ 🔄 4. 시뮬레이션 실행 (SUMO Runner)       진행 중    │     │
│  │    ██████████████░░░░░░░░░░ 60% (720/1200)         │     │
│  │    └─ 실시간: 차량 720대 완료, 평균 속도 25 km/h    │     │
│  │                                                      │     │
│  │ ⏳ 5. KPI 분석 (Analyzer)                대기 중     │     │
│  │                                                      │     │
│  │ ⏳ 6. 리포트 생성 (Reporter)              대기 중     │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  실시간 로그                              [전체 로그 보기]    │
│  ┌─────────────────────────────────────────────────────┐     │
│  │ 12:35:20 INFO  SUMO simulation started              │     │
│  │ 12:35:25 INFO  Vehicle 500 completed route          │     │
│  │ 12:35:30 WARN  Congestion detected at junction_42   │     │
│  │ 12:35:35 INFO  Vehicle 720 completed route          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                               │
│  [일시 정지] [취소]                                           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 5. 결과 대시보드 (/experiments/:id/results)

```
┌───────────────────────────────────────────────────────────────┐
│ 📊 실험 결과: exp-20260508-001                                │
│                                                               │
│ [개요] [KPI 대시보드] [상세 데이터] [리포트] [비교]           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  🎯 주요 지표 비교 (Baseline vs Variant)                      │
│                                                               │
│  ┌─────────────────┬────────────┬────────────┬──────────┐   │
│  │ 지표             │ Baseline   │ +20% 수요  │ 변화율   │   │
│  ├─────────────────┼────────────┼────────────┼──────────┤   │
│  │ 평균 통행 시간   │ 280.5초    │ 350.2초    │ +24.8%  │   │
│  │ 평균 대기 시간   │ 43.1초     │ 62.5초     │ +45.0%  │   │
│  │ 처리량           │ 1,000대/시 │ 850대/시   │ -15.0%  │   │
│  │ 완료율           │ 98.5%      │ 95.2%      │ -3.4%   │   │
│  │ 혼잡도 지수      │ 0.45       │ 0.75       │ +66.7%  │   │
│  └─────────────────┴────────────┴────────────┴──────────┘   │
│                                                               │
│  📈 시각화                                                    │
│                                                               │
│  ┌─ 시간대별 평균 통행 시간 ──────────────────────────┐      │
│  │     (초)                                            │      │
│  │ 400 │                           ╱╲                  │      │
│  │ 350 │                      ╱───╯  ╲                 │      │
│  │ 300 │            ╱────────╯       ╲────             │      │
│  │ 250 │  ────────╯                       ╲────        │      │
│  │     ├────────────────────────────────────────────   │      │
│  │     0    15    30    45    60 (분)                  │      │
│  │     ─ Baseline   ─ +20% 수요                        │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                               │
│  ┌─ 구간별 평균 속도 ──────────────────────────────────┐      │
│  │     (km/h)                                          │      │
│  │  60 │ ██     ██                                     │      │
│  │  40 │ ██ ▓▓  ██ ▓▓                                  │      │
│  │  20 │ ██ ▓▓  ██ ▓▓  ██ ▓▓                           │      │
│  │   0 │ A1 A1  A2 A2  A3 A3  ...                      │      │
│  │     ██ Baseline   ▓▓ +20% 수요                      │      │
│  └─────────────────────────────────────────────────────┘      │
│                                                               │
│  💡 AI 인사이트                                               │
│  • 교통량 20% 증가 시 평균 통행 시간이 25% 증가하여 비선형적  │
│    혼잡 발생                                                  │
│  • 대기 시간이 45% 급증하여 신호 최적화 필요                  │
│  • 오전 7:30-7:45 구간에서 병목 현상 심화                    │
│                                                               │
│  [리포트 다운로드 (PDF)] [데이터 다운로드 (CSV)]              │
│  [다른 실험과 비교] [시나리오 수정하여 재실행]                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 6. 실험 목록 (/experiments)

```
┌───────────────────────────────────────────────────────────────┐
│ 📋 실험 목록                                 [+ 새 실험 생성] │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  필터: [전체 ▼] [상태 ▼] [날짜 ▼]            🔍 검색          │
│                                                               │
│  ┌───┬──────────┬────────────────┬───────┬──────┬──────┐    │
│  │ID │ 이름      │ 생성일          │ 상태  │ 비용  │ 액션 │    │
│  ├───┼──────────┼────────────────┼───────┼──────┼──────┤    │
│  │001│ 강남역 20%│ 2026-05-08 12:00│ ✅완료│ $0.05│ 보기 │    │
│  │002│ 신호 최적│ 2026-05-08 10:30│ 🔄실행│ -    │ 모니터│    │
│  │003│ 차선 확장│ 2026-05-07 15:20│ ✅완료│ $0.06│ 보기 │    │
│  │004│ 좌회전 신호│2026-05-07 09:15│ ❌실패│ $0.02│ 재실행│    │
│  └───┴──────────┴────────────────┴───────┴──────┴──────┘    │
│                                                               │
│  [1] 2 3 ... 10                           총 156개 실험       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 7. 실험 비교 (/experiments/compare)

```
┌───────────────────────────────────────────────────────────────┐
│ 🔀 실험 비교                                                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  비교 대상 선택                                               │
│  [exp-001: 강남역 20% ▼]  vs  [exp-005: 강남역 30% ▼]       │
│                                                               │
│  ┌─────────────────┬────────────┬────────────┬──────────┐   │
│  │ 지표             │ +20% 수요  │ +30% 수요  │ 차이     │   │
│  ├─────────────────┼────────────┼────────────┼──────────┤   │
│  │ 평균 통행 시간   │ 350.2초    │ 485.7초    │ +38.7%  │   │
│  │ 평균 대기 시간   │ 62.5초     │ 105.3초    │ +68.5%  │   │
│  │ 처리량           │ 850대/시   │ 680대/시   │ -20.0%  │   │
│  └─────────────────┴────────────┴────────────┴──────────┘   │
│                                                               │
│  📊 차트 비교                                                 │
│  [시간대별 통행 시간] [구간별 속도] [혼잡도 히트맵]           │
│                                                               │
│  💡 비교 인사이트                                             │
│  • 수요 30% 증가 시 시스템 포화 상태 진입                     │
│  • 20% → 30% 증가 시 비선형적 성능 저하 (38.7% 악화)         │
│  • 신호 최적화 또는 도로 확장 필요                            │
│                                                               │
│  [비교 리포트 다운로드]                                       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 주요 컴포넌트

### 컴포넌트 트리

```
App (Next.js App Router)
├── Layout
│   ├── Header
│   │   ├── Logo
│   │   ├── Navigation
│   │   └── UserMenu
│   ├── Sidebar (optional)
│   └── Footer
│
├── Pages
│   ├── DashboardPage
│   │   ├── StatCards
│   │   ├── RecentExperiments
│   │   └── QuickStartTemplates
│   │
│   ├── NewExperimentPage
│   │   ├── NaturalLanguageInput
│   │   ├── AIScenarioGenerator
│   │   └── ScenarioReviewForm
│   │
│   ├── ExperimentRunningPage
│   │   ├── PipelineProgressTracker
│   │   ├── RealtimeLogViewer
│   │   └── StageDetails
│   │
│   ├── ExperimentResultsPage
│   │   ├── KPIDashboard
│   │   ├── ChartsGrid
│   │   ├── AIInsights
│   │   └── ActionButtons
│   │
│   ├── ExperimentsListPage
│   │   ├── FilterBar
│   │   ├── ExperimentsTable
│   │   └── Pagination
│   │
│   └── CompareExperimentsPage
│       ├── ExperimentSelector
│       ├── ComparisonTable
│       └── ComparisonCharts
│
└── Shared Components
    ├── Chart
    │   ├── LineChart
    │   ├── BarChart
    │   ├── HeatMap
    │   └── MapView
    │
    ├── Form
    │   ├── TextInput
    │   ├── TextArea
    │   ├── Select
    │   └── Checkbox
    │
    ├── UI
    │   ├── Button
    │   ├── Card
    │   ├── Badge
    │   ├── Progress
    │   ├── Toast
    │   └── Modal
    │
    └── Data
        ├── LoadingSpinner
        ├── ErrorBoundary
        └── EmptyState
```

### 핵심 컴포넌트 상세

#### 1. NaturalLanguageInput

```typescript
// components/NaturalLanguageInput.tsx
interface NaturalLanguageInputProps {
  onSubmit: (text: string) => Promise<void>;
  isLoading: boolean;
}

export function NaturalLanguageInput({ onSubmit, isLoading }: Props) {
  const [text, setText] = useState('');
  
  return (
    <div className="space-y-4">
      <TextArea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="교통 시뮬레이션 요구사항을 자유롭게 입력하세요..."
        rows={5}
      />
      
      <div className="flex gap-2">
        <Button 
          onClick={() => onSubmit(text)}
          disabled={!text.trim() || isLoading}
        >
          {isLoading ? '생성 중...' : 'AI 시나리오 생성'}
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger>
            <Button variant="outline">예시 보기</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => setText(example1)}>
              교통량 증가 분석
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setText(example2)}>
              신호 최적화
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}
```

#### 2. PipelineProgressTracker

```typescript
// components/PipelineProgressTracker.tsx
interface Stage {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration?: number;
  progress?: number;
  details?: string;
}

interface PipelineProgressTrackerProps {
  experimentId: string;
}

export function PipelineProgressTracker({ experimentId }: Props) {
  const { data: stages } = useQuery({
    queryKey: ['pipeline-progress', experimentId],
    queryFn: () => fetchPipelineProgress(experimentId),
    refetchInterval: 2000, // 2초마다 폴링
  });
  
  // 또는 SSE 사용
  useEffect(() => {
    const eventSource = new EventSource(
      `/api/pipeline/${experimentId}/progress`
    );
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateProgress(data);
    };
    
    return () => eventSource.close();
  }, [experimentId]);
  
  return (
    <div className="space-y-4">
      {stages.map((stage) => (
        <StageCard key={stage.name} stage={stage} />
      ))}
    </div>
  );
}
```

#### 3. KPIDashboard

```typescript
// components/KPIDashboard.tsx
interface KPIDashboardProps {
  experimentId: string;
  baselineData: KPIData;
  variantData: KPIData;
}

export function KPIDashboard({ experimentId, baselineData, variantData }: Props) {
  return (
    <div className="space-y-6">
      {/* 요약 카드 */}
      <div className="grid grid-cols-4 gap-4">
        <KPICard
          label="평균 통행 시간"
          baseline={baselineData.avg_travel_time}
          variant={variantData.avg_travel_time}
          unit="초"
        />
        <KPICard
          label="평균 대기 시간"
          baseline={baselineData.avg_waiting_time}
          variant={variantData.avg_waiting_time}
          unit="초"
        />
        {/* ... */}
      </div>
      
      {/* 차트 그리드 */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>시간대별 평균 통행 시간</CardHeader>
          <CardContent>
            <LineChart
              data={timeSeriesData}
              xKey="time"
              lines={[
                { key: 'baseline', color: 'blue', label: 'Baseline' },
                { key: 'variant', color: 'red', label: '+20% 수요' },
              ]}
            />
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>구간별 평균 속도</CardHeader>
          <CardContent>
            <BarChart
              data={segmentData}
              xKey="segment"
              bars={[
                { key: 'baseline', color: 'blue' },
                { key: 'variant', color: 'red' },
              ]}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

#### 4. MapView (OpenStreetMap)

```typescript
// components/MapView.tsx
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';

interface MapViewProps {
  center: [number, number]; // [lat, lng]
  bbox?: [number, number, number, number]; // [minLng, minLat, maxLng, maxLat]
  network?: NetworkData;
}

export function MapView({ center, bbox, network }: MapViewProps) {
  return (
    <MapContainer center={center} zoom={13} style={{ height: '400px' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      
      {/* 도로망 표시 */}
      {network?.edges.map((edge) => (
        <Polyline key={edge.id} positions={edge.shape} color="blue" />
      ))}
      
      {/* 교차로 표시 */}
      {network?.junctions.map((junction) => (
        <Marker key={junction.id} position={junction.position}>
          <Popup>{junction.id}</Popup>
        </Marker>
      ))}
      
      {/* BBox 표시 */}
      {bbox && <Rectangle bounds={[[bbox[1], bbox[0]], [bbox[3], bbox[2]]]} />}
    </MapContainer>
  );
}
```

---

## 백엔드 연동

### API Client

```typescript
// lib/api-client.ts
import { QueryClient } from '@tanstack/react-query';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
  // Pipeline
  async runPipeline(request: PipelineRequest) {
    const res = await fetch(`${API_BASE_URL}/pipeline/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return res.json();
  },
  
  async getPipelineProgress(executionId: string) {
    const res = await fetch(`${API_BASE_URL}/pipeline/${executionId}/progress`);
    return res.json();
  },
  
  // Agent Service
  async parseUserRequest(request: string) {
    const res = await fetch(`${API_BASE_URL}/orchestrator/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_request: request }),
    });
    return res.json();
  },
  
  async buildScenario(request: ScenarioBuildRequest) {
    const res = await fetch(`${API_BASE_URL}/scenario/build`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return res.json();
  },
  
  // Experiments (향후 DB 연동)
  async listExperiments(filters?: ExperimentFilters) {
    const params = new URLSearchParams(filters as any);
    const res = await fetch(`${API_BASE_URL}/experiments?${params}`);
    return res.json();
  },
  
  async getExperiment(id: string) {
    const res = await fetch(`${API_BASE_URL}/experiments/${id}`);
    return res.json();
  },
  
  async getExperimentResults(id: string) {
    const res = await fetch(`${API_BASE_URL}/experiments/${id}/results`);
    return res.json();
  },
};
```

### React Query Hooks

```typescript
// hooks/useExperiments.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

export function useRunPipeline() {
  return useMutation({
    mutationFn: apiClient.runPipeline,
    onSuccess: (data) => {
      // Redirect to monitoring page
      router.push(`/experiments/${data.execution_id}/running`);
    },
  });
}

export function usePipelineProgress(executionId: string) {
  return useQuery({
    queryKey: ['pipeline-progress', executionId],
    queryFn: () => apiClient.getPipelineProgress(executionId),
    refetchInterval: (data) => {
      // 완료되면 폴링 중지
      return data?.status === 'completed' ? false : 2000;
    },
  });
}

export function useExperiments(filters?: ExperimentFilters) {
  return useQuery({
    queryKey: ['experiments', filters],
    queryFn: () => apiClient.listExperiments(filters),
  });
}

export function useExperimentResults(experimentId: string) {
  return useQuery({
    queryKey: ['experiment-results', experimentId],
    queryFn: () => apiClient.getExperimentResults(experimentId),
  });
}
```

### Server-Sent Events (실시간 진행률)

```typescript
// hooks/usePipelineProgressSSE.ts
import { useEffect, useState } from 'react';

interface PipelineProgress {
  execution_id: string;
  status: 'running' | 'completed' | 'failed';
  current_stage: string;
  progress: number;
  stages: StageStatus[];
}

export function usePipelineProgressSSE(executionId: string) {
  const [progress, setProgress] = useState<PipelineProgress | null>(null);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const eventSource = new EventSource(
      `${API_BASE_URL}/pipeline/${executionId}/progress/stream`
    );
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data);
      
      // 완료 시 연결 종료
      if (data.status === 'completed' || data.status === 'failed') {
        eventSource.close();
      }
    };
    
    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      setError(new Error('Connection lost'));
      eventSource.close();
    };
    
    return () => {
      eventSource.close();
    };
  }, [executionId]);
  
  return { progress, error };
}
```

---

## 상태 관리

### Zustand Store (Client State)

```typescript
// store/experiment-store.ts
import { create } from 'zustand';

interface ExperimentState {
  // 현재 생성 중인 실험
  currentExperiment: {
    userRequest: string;
    scenario: ScenarioSpec | null;
    isGenerating: boolean;
  };
  
  // 액션
  setUserRequest: (request: string) => void;
  setScenario: (scenario: ScenarioSpec) => void;
  clearExperiment: () => void;
}

export const useExperimentStore = create<ExperimentState>((set) => ({
  currentExperiment: {
    userRequest: '',
    scenario: null,
    isGenerating: false,
  },
  
  setUserRequest: (request) => set((state) => ({
    currentExperiment: { ...state.currentExperiment, userRequest: request }
  })),
  
  setScenario: (scenario) => set((state) => ({
    currentExperiment: { ...state.currentExperiment, scenario }
  })),
  
  clearExperiment: () => set({
    currentExperiment: { userRequest: '', scenario: null, isGenerating: false }
  }),
}));
```

### Form State (React Hook Form + Zod)

```typescript
// components/ScenarioEditForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const scenarioSchema = z.object({
  location: z.object({
    name: z.string(),
    bbox: z.array(z.number()).length(4),
    center: z.array(z.number()).length(2),
  }),
  simulation_config: z.object({
    duration_hours: z.number().min(0.25).max(24),
    time_step: z.number().min(0.1).max(10),
    start_time: z.string(),
  }),
  baseline: z.object({
    vehicle_count: z.number().min(1),
    vehicle_types: z.array(z.string()),
  }),
  variants: z.array(z.object({
    variant_id: z.string(),
    description: z.string(),
    parameters: z.record(z.any()),
  })),
});

type ScenarioFormData = z.infer<typeof scenarioSchema>;

export function ScenarioEditForm({ initialData, onSubmit }: Props) {
  const form = useForm<ScenarioFormData>({
    resolver: zodResolver(scenarioSchema),
    defaultValues: initialData,
  });
  
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        {/* Form fields */}
      </form>
    </Form>
  );
}
```

---

## 배포 전략

### Dockerfile

```dockerfile
# apps/frontend/Dockerfile
FROM node:20-alpine AS base

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1
RUN corepack enable pnpm && pnpm build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### Kubernetes Deployment

```yaml
# k8s/apps/frontend/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: agent-t
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t/frontend:v0.4.0
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "http://pipeline.agent-t.svc.cluster.local:8000"
        - name: NODE_ENV
          value: "production"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: agent-t
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: frontend
  namespace: agent-t
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  ingressClassName: alb
  rules:
  - host: agent-t.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### Helm Chart

```yaml
# infra/helm/services/frontend/values.yaml
replicaCount: 2

image:
  repository: <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/agent-t/frontend
  tag: v0.4.0
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80
  targetPort: 3000

ingress:
  enabled: true
  className: alb
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
  hosts:
    - host: agent-t.example.com
      paths:
        - path: /
          pathType: Prefix

env:
  - name: NEXT_PUBLIC_API_URL
    value: "http://pipeline.agent-t.svc.cluster.local:8000"
  - name: NODE_ENV
    value: "production"

resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

---

## 개발 로드맵

### Phase 1: 기본 UI (2-3주)

**Week 1-2**: 핵심 페이지
- [ ] Layout + Navigation
- [ ] Dashboard (홈)
- [ ] New Experiment (자연어 입력 + AI 시나리오 생성)
- [ ] Experiment Running (진행률 표시)
- [ ] Experiment Results (기본 KPI 테이블)

**Week 3**: 백엔드 연동
- [ ] API Client 구현
- [ ] React Query 설정
- [ ] 에러 처리
- [ ] 로딩 상태

**결과물**: 기본 E2E 플로우 동작

---

### Phase 2: 고급 기능 (2-3주)

**Week 4-5**: 데이터 시각화
- [ ] Chart 컴포넌트 (Line, Bar, HeatMap)
- [ ] KPI Dashboard 고도화
- [ ] Map View (OpenStreetMap)
- [ ] 실시간 진행률 (SSE)

**Week 6**: 실험 관리
- [ ] Experiments List (필터링, 검색)
- [ ] Experiment Compare
- [ ] Report Viewer (Markdown)
- [ ] Export (PDF, CSV)

**결과물**: 프로덕션 준비 완료

---

### Phase 3: 최적화 & 배포 (1-2주)

**Week 7**: 성능 최적화
- [ ] Code Splitting
- [ ] Image Optimization
- [ ] SSR/ISR 적용
- [ ] Lighthouse 점수 90+ 달성

**Week 8**: 배포
- [ ] Docker 이미지 빌드
- [ ] Kubernetes 배포
- [ ] Helm Chart 작성
- [ ] Argo CD 연동
- [ ] 프로덕션 테스트

**결과물**: AWS 프로덕션 배포 완료

---

### Phase 4: 고도화 (향후)

**추가 기능**:
- [ ] 사용자 인증 (Cognito)
- [ ] 권한 관리 (RBAC)
- [ ] 템플릿 시스템
- [ ] 협업 기능 (공유, 댓글)
- [ ] 알림 시스템 (이메일, Slack)
- [ ] 고급 분석 (A/B 테스트, 민감도 분석)
- [ ] AI 추천 (다음 실험 제안)

---

## 기대 효과

### 사용자 관점

| Before (API만) | After (UI 추가) |
|----------------|-----------------|
| curl 명령어 필요 | 웹 브라우저만 있으면 OK |
| JSON 수동 작성 | 자연어 입력 |
| 결과 JSON 파싱 | 인터랙티브 차트 |
| 실험 추적 어려움 | 히스토리 자동 저장 |
| 비교 분석 수동 | 원클릭 비교 |

### 비즈니스 관점

- **접근성 향상**: 개발자 외 정책 입안자도 사용 가능
- **생산성 향상**: 실험 생성 시간 10분 → 2분
- **의사결정 지원**: 시각화된 데이터로 빠른 인사이트
- **확장성**: 템플릿, 협업 기능 추가 가능

---

## 참고 자료

### 유사 프로젝트

- **Streamlit**: Python 기반 데이터 앱
- **Retool**: Low-code 내부 툴 빌더
- **AWS Management Console**: 클라우드 리소스 관리 UI

### 디자인 참고

- **Vercel Dashboard**: 깔끔한 모던 UI
- **Linear**: 미니멀 디자인 + 빠른 성능
- **Notion**: 직관적인 UX

---

**작성일**: 2026-05-08  
**버전**: 0.4.0  
**상태**: 계획 단계 (구현 예정)
