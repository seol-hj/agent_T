'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Download, BarChart3 } from 'lucide-react';

export default function ExperimentResultsPage({ 
  params 
}: { 
  params: { id: string } 
}) {
  const router = useRouter();

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/')}
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              대시보드
            </Button>
          </div>
          <h2 className="text-3xl font-bold tracking-tight">실험 결과</h2>
          <p className="text-muted-foreground mt-1">
            Execution ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{params.id}</code>
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" />
            리포트 다운로드
          </Button>
        </div>
      </div>

      {/* Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <BarChart3 className="mr-2 h-5 w-5" />
            KPI 대시보드
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-2 border-dashed rounded-lg p-12 text-center">
            <p className="text-lg font-medium text-muted-foreground mb-2">
              🚧 KPI 대시보드 구현 예정
            </p>
            <p className="text-sm text-muted-foreground">
              실험 결과 차트, KPI 테이블, AI 인사이트가 여기 표시됩니다
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Mock Data */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">평균 통행 시간</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">350.2초</div>
            <p className="text-sm text-muted-foreground">+24.8% vs 기준선</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">평균 대기 시간</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">62.5초</div>
            <p className="text-sm text-muted-foreground">+45.0% vs 기준선</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">처리량</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">850대/시</div>
            <p className="text-sm text-muted-foreground">-15.0% vs 기준선</p>
          </CardContent>
        </Card>
      </div>

      {/* Actions */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Button onClick={() => router.push('/experiments/new')}>
              새 실험 시작
            </Button>
            <Button variant="outline">
              이 시나리오 재실행
            </Button>
            <Button variant="outline">
              다른 실험과 비교
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
