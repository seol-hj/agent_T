# AI Agent T - Frontend

Next.js 14 기반 프론트엔드 애플리케이션

## 빠른 시작

```bash
# 의존성 설치
pnpm install

# 개발 서버 실행
pnpm dev

# http://localhost:3000 접속
```

## 개발 환경 설정

### 백엔드 연동

`.env.local` 파일 생성:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 백엔드 서비스 실행

```bash
# 프로젝트 루트에서
docker compose up -d

# 백엔드 API: http://localhost:8000
```

## 기술 스택

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5
- **Styling**: TailwindCSS 3
- **State Management**: React Query + Zustand
- **UI Components**: Custom (shadcn/ui 스타일)

## 프로젝트 구조

```
src/
├── app/                    # Next.js App Router 페이지
│   ├── page.tsx           # 홈 (대시보드)
│   ├── experiments/
│   │   ├── new/
│   │   │   └── page.tsx   # 새 실험 생성
│   │   └── [id]/
│   │       ├── running/
│   │       │   └── page.tsx  # 실행 중
│   │       └── results/
│   │           └── page.tsx  # 결과
│   ├── layout.tsx         # 루트 레이아웃
│   ├── providers.tsx      # React Query Provider
│   └── globals.css        # 글로벌 스타일
│
├── components/             # React 컴포넌트
│   ├── ui/                # 기본 UI 컴포넌트
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── NaturalLanguageInput.tsx
│   ├── PipelineProgress.tsx
│   └── ...
│
├── lib/                    # 유틸리티
│   ├── api-client.ts      # API 클라이언트
│   ├── query-client.ts    # React Query 설정
│   └── utils.ts           # 헬퍼 함수
│
├── hooks/                  # Custom Hooks
│   └── usePipeline.ts     # 파이프라인 관련 hooks
│
├── types/                  # TypeScript 타입
│   └── index.ts           # 공통 타입 정의
│
└── store/                  # Zustand Store
    └── experiment-store.ts
```

## 주요 기능

### 1. 자연어 입력
사용자가 자연어로 교통 시뮬레이션 요구사항을 입력하면 AI가 자동으로 시나리오를 생성합니다.

### 2. 실시간 모니터링
시뮬레이션 실행 중 진행률을 실시간으로 확인할 수 있습니다 (2초마다 폴링).

### 3. KPI 대시보드
시뮬레이션 결과를 차트와 테이블로 시각화합니다.

## 개발 가이드

상세한 구현 가이드는 다음 문서를 참고하세요:

- [프론트엔드 구현 가이드](../../docs/frontend-implementation-guide.md)
- [프론트엔드 계획](../../docs/frontend-plan.md)

## 빌드

```bash
# 프로덕션 빌드
pnpm build

# 프로덕션 서버 실행
pnpm start
```

## Docker

```bash
# 이미지 빌드
docker build -t agent-t-frontend:latest .

# 컨테이너 실행
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 agent-t-frontend:latest
```

## 다음 단계

1. ✅ 프로젝트 설정 완료
2. 🔄 UI 컴포넌트 구현 (진행 중)
3. ⏳ 페이지 구현
4. ⏳ 백엔드 연동 테스트
5. ⏳ Docker Compose 통합

---

**버전**: 0.4.0  
**상태**: 개발 중
