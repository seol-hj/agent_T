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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleSubmit();
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
          onKeyDown={handleKeyDown}
          placeholder="예: 강남역에서 교통량이 20% 증가하면 평균 통행 시간은?"
          className="w-full min-h-[120px] p-3 border border-input rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring resize-none"
          disabled={isLoading}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Ctrl+Enter를 누르면 즉시 생성합니다
        </p>
      </div>

      <div className="flex gap-2">
        <Button
          onClick={handleSubmit}
          disabled={!text.trim() || isLoading}
          size="lg"
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

        {text && (
          <Button
            onClick={() => setText('')}
            variant="outline"
            disabled={isLoading}
          >
            초기화
          </Button>
        )}
      </div>

      <div className="space-y-2 border-t pt-4">
        <p className="text-sm font-medium text-muted-foreground">예시 템플릿:</p>
        <div className="space-y-1">
          {examples.map((example, i) => (
            <button
              key={i}
              onClick={() => setText(example)}
              className="block w-full text-left text-sm text-primary hover:underline disabled:opacity-50 disabled:cursor-not-allowed p-2 rounded hover:bg-accent transition-colors"
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
