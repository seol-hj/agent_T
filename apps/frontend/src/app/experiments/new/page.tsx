'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { NaturalLanguageInput } from '@/components/NaturalLanguageInput';
import { useRunPipeline } from '@/hooks/usePipeline';
import { AlertCircle } from 'lucide-react';

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
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">새 실험 생성</h2>
        <p className="text-muted-foreground mt-2">
          자연어로 교통 시뮬레이션 요구사항을 입력하세요. AI가 자동으로 시나리오를 생성합니다.
        </p>
      </div>

      {/* Input Card */}
      <Card>
        <CardHeader>
          <CardTitle>1. 자연어 요구사항 입력</CardTitle>
          <CardDescription>
            교통 시뮬레이션에서 알고 싶은 내용을 자유롭게 입력하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <NaturalLanguageInput
            onSubmit={handleSubmit}
            isLoading={runPipeline.isPending}
          />
        </CardContent>
      </Card>

      {/* Error Display */}
      {runPipeline.isError && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center">
              <AlertCircle className="mr-2 h-5 w-5" />
              오류 발생
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              {runPipeline.error?.message || '알 수 없는 오류가 발생했습니다.'}
            </p>
            <div className="mt-4 p-3 rounded-md bg-muted text-xs font-mono">
              Request ID: {requestId}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="border-blue-200 bg-blue-50/50">
        <CardHeader>
          <CardTitle className="text-lg">💡 작동 원리</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p><strong>1단계:</strong> AI가 자연어를 분석하여 구조화된 시나리오 생성</p>
          <p><strong>2단계:</strong> OpenStreetMap에서 도로망 데이터 추출</p>
          <p><strong>3단계:</strong> SUMO 시뮬레이터로 교통 흐름 계산</p>
          <p><strong>4단계:</strong> 21가지 KPI 자동 분석</p>
          <p><strong>5단계:</strong> 정책 리포트 생성</p>
          <p className="text-muted-foreground pt-2">
            예상 소요 시간: 2-3분 (로컬 테스트 모드)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
