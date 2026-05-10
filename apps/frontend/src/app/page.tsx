'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Plus, Activity, CheckCircle, Zap } from 'lucide-react';
import { useHealthCheck } from '@/hooks/usePipeline';

export default function HomePage() {
  const router = useRouter();
  const { data: health } = useHealthCheck();

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="flex flex-col items-center justify-center text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          AI 기반 교통 시뮬레이션
        </h1>
        <p className="max-w-[700px] text-lg text-muted-foreground">
          자연어로 교통 시뮬레이션 요구사항을 입력하면 AI가 자동으로 실험을 생성하고 분석합니다
        </p>
        <div className="flex gap-4 mt-4">
          <Button size="lg" onClick={() => router.push('/experiments/new')}>
            <Plus className="mr-2 h-5 w-5" />
            새 실험 시작하기
          </Button>
        </div>
      </div>

      {/* Status */}
      {health && (
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span>백엔드 서비스 정상 ({health.service})</span>
        </div>
      )}

      {/* Features */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <Zap className="h-10 w-10 text-blue-500 mb-2" />
            <CardTitle>AI 자동 생성</CardTitle>
            <CardDescription>
              자연어 입력만으로 시뮬레이션 시나리오를 자동 생성
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              복잡한 설정 없이 "강남역에서 교통량 20% 증가 시뮬레이션"처럼 자연스럽게 입력하세요
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Activity className="h-10 w-10 text-green-500 mb-2" />
            <CardTitle>실시간 모니터링</CardTitle>
            <CardDescription>
              시뮬레이션 진행 상황을 실시간으로 확인
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              6단계 파이프라인의 진행률을 실시간으로 모니터링하고 결과를 즉시 확인하세요
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CheckCircle className="h-10 w-10 text-violet-500 mb-2" />
            <CardTitle>KPI 자동 분석</CardTitle>
            <CardDescription>
              21가지 교통 지표를 자동으로 분석
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              평균 통행 시간, 대기 시간, 처리량 등 주요 KPI를 차트와 함께 제공합니다
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Start */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle>빠른 시작</CardTitle>
          <CardDescription>
            첫 번째 교통 시뮬레이션을 시작해보세요
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium">예시 요구사항:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 강남역 일대에서 교통량이 20% 증가했을 때 평균 통행 시간은?</li>
              <li>• 신호등 대기 시간을 10초 줄이면 전체 통행 시간이 얼마나 감소하나요?</li>
              <li>• 2차로를 3차로로 확장하면 처리량이 얼마나 증가하나요?</li>
            </ul>
          </div>
          
          <Button
            onClick={() => router.push('/experiments/new')}
            className="w-full"
            size="lg"
          >
            지금 시작하기
          </Button>
        </CardContent>
      </Card>

      {/* Info */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">로컬 개발 모드</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>• MockLLM 사용 (실제 AI 호출 없음)</p>
            <p>• LocalStorage 사용 (파일 시스템 저장)</p>
            <p>• dry_run 모드 (빠른 테스트)</p>
            <p>• 비용: 무료</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">프로덕션 모드</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-2">
            <p>• Bedrock Claude 3.5 Sonnet</p>
            <p>• S3 스토리지</p>
            <p>• 실제 SUMO 시뮬레이션</p>
            <p>• AWS 인프라 필요</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
