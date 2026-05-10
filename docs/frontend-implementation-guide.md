# 프론트엔드 구현 가이드

AI Agent T 프론트엔드 단계별 구현 가이드

---

## 🎯 목표

**로컬에서 백엔드 API와 연동되는 프론트엔드를 구현하여 전체 E2E 플로우 테스트**

---

## 📋 Phase 1: 프로젝트 설정 (완료 ✅)

### 생성된 파일

```
apps/frontend/
├── package.json          ✅ 의존성 정의
├── tsconfig.json         ✅ TypeScript 설정
├── next.config.js        ✅ Next.js 설정
├── tailwind.config.ts    ✅ TailwindCSS 설정
├── postcss.config.js     ✅ PostCSS 설정
└── src/
    ├── app/
    │   └── globals.css   ✅ 글로벌 스타일
    ├── components/       (다음 단계)
    ├── lib/              (다음 단계)
    ├── hooks/            (다음 단계)
    ├── types/            (다음 단계)
    └── store/            (다음 단계)
```

### 다음: 의존성 설치

```bash
cd apps/frontend
npm install
# 또는
pnpm install
```

---

## 📦 Phase 2: 핵심 파일 구조

### 2.1 타입 정의

**src/types/index.ts**:

```typescript
// 백엔드 API 응답 타입 (Pydantic 스키마와 일치)
export interface PipelineExecutionRequest {
  request_id: string;
  user_request: string;
  dry_run: boolean;
  skip_steps?: string[];
}

export interface PipelineExecutionResult {
  schema_version: string;
  execution_id: string;
  request_id: string;
  experiment_id: string;
  status: 'completed' | 'failed' | 'partial';
  steps: PipelineStepStatus[];
  report_uri?: string;
  started_at: string;
  completed_at?: string;
  total_duration_ms?: number;
  error_message?: string;
}

export interface PipelineStepStatus {
  step_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  artifact_uri?: string;
  error_message?: string;
}

export interface ScenarioSpec {
  experiment_id: string;
  scenario_type: string;
  location: {
    name: string;
    bbox: [number, number, number, number];
    center: [number, number];
  };
  simulation_config: {
    duration_hours: number;
    time_step: number;
    start_time: string;
  };
  baseline: {
    vehicle_count: number;
    vehicle_types: string[];
  };
  variants: Array<{
    variant_id: string;
    description: string;
    parameters: Record<string, any>;
  }>;
  kpis: string[];
  objectives: string[];
}

export interface KPIData {
  avg_travel_time: number;
  avg_waiting_time: number;
  throughput: number;
  completion_rate: number;
  congestion_index: number;
}
```

### 2.2 API Client

**src/lib/api-client.ts**:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Pipeline
  async runPipeline(request: PipelineExecutionRequest): Promise<PipelineExecutionResult> {
    return this.request('/pipeline/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getPipelineProgress(executionId: string): Promise<PipelineExecutionResult> {
    return this.request(`/pipeline/${executionId}/status`);
  }

  // Scenario
  async parseUserRequest(userRequest: string) {
    return this.request('/orchestrator/parse', {
      method: 'POST',
      body: JSON.stringify({ user_request: userRequest }),
    });
  }

  async buildScenario(request: any) {
    return this.request('/scenario/build', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Health
  async healthCheck() {
    return this.request('/health');
  }
}

export const apiClient = new APIClient(API_BASE_URL);
```

### 2.3 React Query 설정

**src/lib/query-client.ts**:

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5분
    },
  },
});
```

**src/app/providers.tsx**:

```typescript
'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query-client';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### 2.4 Custom Hooks

**src/hooks/usePipeline.ts**:

```typescript
import { useMutation, useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import type { PipelineExecutionRequest } from '@/types';

export function useRunPipeline() {
  const router = useRouter();

  return useMutation({
    mutationFn: (request: PipelineExecutionRequest) => 
      apiClient.runPipeline(request),
    onSuccess: (data) => {
      router.push(`/experiments/${data.execution_id}/running`);
    },
  });
}

export function usePipelineProgress(executionId: string | null) {
  return useQuery({
    queryKey: ['pipeline-progress', executionId],
    queryFn: () => apiClient.getPipelineProgress(executionId!),
    enabled: !!executionId,
    refetchInterval: (data) => {
      // 완료되면 폴링 중지
      if (!data) return false;
      const isRunning = data.status === 'running' || 
                       data.steps.some(s => s.status === 'running');
      return isRunning ? 2000 : false;
    },
  });
}
```

---

## 🎨 Phase 3: UI 컴포넌트

### 3.1 기본 컴포넌트 (shadcn/ui 스타일)

**src/components/ui/button.tsx**:

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'ghost'
  size?: 'default' | 'sm' | 'lg'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-md font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50",
          {
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
            'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
            'border border-input bg-background hover:bg-accent': variant === 'outline',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
          },
          {
            'h-10 px-4 py-2': size === 'default',
            'h-9 px-3': size === 'sm',
            'h-11 px-8': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)

Button.displayName = "Button"

export { Button }
```

**src/components/ui/card.tsx**:

```typescript
import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border bg-card text-card-foreground shadow-sm",
        className
      )}
      {...props}
    />
  )
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    />
  )
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  )
)
CardTitle.displayName = "CardTitle"

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
)
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardContent }
```

**src/lib/utils.ts**:

```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### 3.2 비즈니스 컴포넌트

**src/components/NaturalLanguageInput.tsx**:

```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';

interface NaturalLanguageInputProps {
  onSubmit: (text: string) => void;
  isLoading?: boolean;
}

export function NaturalLanguageInput({ onSubmit, isLoading }: NaturalLanguageInputProps) {
  const [text, setText] = useState('');

  const examples = [
    "강남역 일대에서 교통량이 20% 증가했을 때 평균 통행 시간은?",
    "신호등 대기 시간을 10초 줄이면 전체 통행 시간이 얼마나 감소하나요?",
    "2차로를 3차로로 확장하면 처리량이 얼마나 증가하나요?",
  ];

  const handleSubmit = () => {
    if (text.trim()) {
      onSubmit(text);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium mb-2">
          교통 시뮬레이션 요구사항을 자유롭게 입력하세요
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="예: 강남역에서 교통량이 20% 증가하면 평균 통행 시간은?"
          className="w-full min-h-[120px] p-3 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={isLoading}
        />
      </div>

      <div className="flex gap-2">
        <Button
          onClick={handleSubmit}
          disabled={!text.trim() || isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              생성 중...
            </>
          ) : (
            'AI 시나리오 생성'
          )}
        </Button>
      </div>

      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">예시:</p>
        <div className="space-y-1">
          {examples.map((example, i) => (
            <button
              key={i}
              onClick={() => setText(example)}
              className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:underline"
              disabled={isLoading}
            >
              • {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**src/components/PipelineProgress.tsx**:

```typescript
'use client';

import { usePipelineProgress } from '@/hooks/usePipeline';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, Loader2, Clock, XCircle } from 'lucide-react';

interface PipelineProgressProps {
  executionId: string;
}

export function PipelineProgress({ executionId }: PipelineProgressProps) {
  const { data, isLoading } = usePipelineProgress(executionId);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!data) {
    return <div>No data</div>;
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>파이프라인 진행 상황</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.steps.map((step, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className="mt-0.5">{getStatusIcon(step.status)}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">{step.step_name}</h4>
                  {step.duration_ms && (
                    <span className="text-sm text-muted-foreground">
                      {(step.duration_ms / 1000).toFixed(1)}초
                    </span>
                  )}
                </div>
                {step.error_message && (
                  <p className="text-sm text-red-500 mt-1">{step.error_message}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 📄 Phase 4: 페이지 구현

### 4.1 루트 레이아웃

**src/app/layout.tsx**:

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Agent T - 교통 시뮬레이션 플랫폼",
  description: "AI 기반 교통 시뮬레이션 자동화 플랫폼",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-background">
            <header className="border-b">
              <div className="container mx-auto px-4 py-4">
                <h1 className="text-2xl font-bold">AI Agent T</h1>
              </div>
            </header>
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
```

### 4.2 홈 (대시보드)

**src/app/page.tsx**:

```typescript
'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plus, Activity, DollarSign, CheckCircle } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">대시보드</h2>
          <p className="text-muted-foreground">
            AI 기반 교통 시뮬레이션 플랫폼
          </p>
        </div>
        <Button onClick={() => router.push('/experiments/new')}>
          <Plus className="mr-2 h-4 w-4" />
          새 실험 생성
        </Button>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 실험 수</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">
              첫 실험을 시작해보세요
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">실행 중</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
            <p className="text-xs text-muted-foreground">
              진행 중인 실험 없음
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">금월 비용</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$0.00</div>
            <p className="text-xs text-muted-foreground">
              비용 발생 없음
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 빠른 시작 */}
      <Card>
        <CardHeader>
          <CardTitle>빠른 시작</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground mb-4">
            자연어로 교통 시뮬레이션 요구사항을 입력하면 AI가 자동으로 실험을 생성합니다.
          </p>
          <Button
            onClick={() => router.push('/experiments/new')}
            className="w-full"
          >
            첫 실험 시작하기
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
```

### 4.3 새 실험 생성

**src/app/experiments/new/page.tsx**:

```typescript
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { NaturalLanguageInput } from '@/components/NaturalLanguageInput';
import { useRunPipeline } from '@/hooks/usePipeline';

export default function NewExperimentPage() {
  const [requestId] = useState(() => `req-${Date.now()}`);
  const runPipeline = useRunPipeline();

  const handleSubmit = (userRequest: string) => {
    runPipeline.mutate({
      request_id: requestId,
      user_request: userRequest,
      dry_run: true, // 로컬 테스트는 dry_run
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">새 실험 생성</h2>
        <p className="text-muted-foreground">
          자연어로 교통 시뮬레이션 요구사항을 입력하세요
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. 자연어 요구사항 입력</CardTitle>
        </CardHeader>
        <CardContent>
          <NaturalLanguageInput
            onSubmit={handleSubmit}
            isLoading={runPipeline.isPending}
          />
        </CardContent>
      </Card>

      {runPipeline.isError && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">오류 발생</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              {runPipeline.error?.message || '알 수 없는 오류가 발생했습니다.'}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

### 4.4 실험 실행 중

**src/app/experiments/[id]/running/page.tsx**:

```typescript
'use client';

import { PipelineProgress } from '@/components/PipelineProgress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { usePipelineProgress } from '@/hooks/usePipeline';

export default function ExperimentRunningPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { data } = usePipelineProgress(params.id);

  // 완료되면 결과 페이지로 이동
  if (data?.status === 'completed') {
    router.push(`/experiments/${params.id}/results`);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">실험 실행 중</h2>
        <p className="text-muted-foreground">
          Experiment ID: {params.id}
        </p>
      </div>

      <PipelineProgress executionId={params.id} />

      {data?.status === 'failed' && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">실험 실패</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm mb-4">{data.error_message}</p>
            <Button
              onClick={() => router.push('/experiments/new')}
              variant="outline"
            >
              새 실험 시작
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

---

## 🐳 Phase 5: Docker & Docker Compose 통합

### 5.1 Dockerfile

**apps/frontend/Dockerfile**:

```dockerfile
# Base
FROM node:20-alpine AS base
RUN corepack enable pnpm

# Dependencies
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN pnpm build

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

### 5.2 docker-compose.yaml 업데이트

**docker-compose.yaml** (frontend 추가):

```yaml
services:
  # ... 기존 서비스들 ...

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: apps/frontend/Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - pipeline
    networks:
      - agent-t

networks:
  agent-t:
    driver: bridge

volumes:
  storage-data:
```

---

## ✅ Phase 6: 로컬 테스트

### 6.1 전체 스택 실행

```bash
# 1. 백엔드 서비스 시작
docker compose up --build -d

# 2. 프론트엔드 개발 서버 (별도 터미널)
cd apps/frontend
pnpm install
pnpm dev

# 브라우저에서 http://localhost:3000 접속
```

### 6.2 E2E 테스트 플로우

1. **홈 접속**: http://localhost:3000
2. **새 실험 생성 클릭**
3. **자연어 입력**:
   ```
   강남역 일대에서 교통량이 20% 증가했을 때 평균 통행 시간은?
   ```
4. **AI 시나리오 생성 버튼 클릭**
5. **실행 모니터링 페이지로 자동 이동**
6. **진행률 실시간 확인** (2초마다 폴링)
7. **완료 후 결과 페이지로 자동 이동**

### 6.3 체크리스트

- [ ] 홈 페이지 정상 렌더링
- [ ] 새 실험 생성 페이지 정상 동작
- [ ] 자연어 입력 → 파이프라인 실행 정상
- [ ] 실행 중 페이지에서 진행률 표시
- [ ] 완료 후 결과 페이지 이동
- [ ] 에러 발생 시 에러 메시지 표시

---

## 🚀 Phase 7: 프로덕션 빌드

### 7.1 프로덕션 빌드 테스트

```bash
cd apps/frontend

# 빌드
pnpm build

# 프로덕션 서버 실행
pnpm start

# http://localhost:3000 접속하여 확인
```

### 7.2 Docker Compose로 전체 스택 테스트

```bash
# 전체 빌드 (프론트엔드 포함)
docker compose up --build

# 접속
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000

# 테스트 스크립트 실행 (백엔드만)
./scripts/test-services-local.sh
```

---

## 📋 다음 단계

### ✅ 로컬 개발 완료 후

1. **AWS 인프라 구축**:
   ```bash
   ./scripts/bootstrap-dev.sh
   ```

2. **프론트엔드 ECR Push**:
   ```bash
   cd apps/frontend
   docker build -t frontend:latest .
   docker tag frontend:latest <ecr-url>/agent-t/frontend:v0.4.0
   docker push <ecr-url>/agent-t/frontend:v0.4.0
   ```

3. **Kubernetes 배포**:
   ```bash
   cd infra/helm/services/frontend
   helm install frontend . --namespace agent-t
   ```

4. **Ingress 설정**:
   - 프론트엔드: https://agent-t.example.com
   - 백엔드 API: https://api.agent-t.example.com

---

## 🛠️ 개발 팁

### Hot Reload

프론트엔드 개발 중에는 Docker Compose를 사용하지 말고 로컬 dev 서버를 사용하세요:

```bash
# 백엔드만 Docker로
docker compose up -d

# 프론트엔드는 로컬 dev
cd apps/frontend
pnpm dev
```

이렇게 하면 코드 변경 시 즉시 반영됩니다.

### API 에러 디버깅

```typescript
// src/lib/api-client.ts에 로깅 추가
console.log('Request:', { url, method, body });
console.log('Response:', { status, data });
```

### 타입 불일치 해결

백엔드 Pydantic 스키마가 변경되면 프론트엔드 타입도 함께 업데이트:

```bash
# 백엔드에서 OpenAPI 스키마 export (향후)
# 프론트엔드에서 타입 자동 생성 (향후)
```

---

## 📚 참고 문서

- [Next.js 14 문서](https://nextjs.org/docs)
- [TailwindCSS 문서](https://tailwindcss.com/docs)
- [React Query 문서](https://tanstack.com/query/latest)
- [shadcn/ui 컴포넌트](https://ui.shadcn.com/)

---

**작성일**: 2026-05-08  
**버전**: 0.4.0  
**상태**: 구현 가이드
