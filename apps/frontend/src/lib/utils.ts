import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * TailwindCSS 클래스 병합 유틸리티
 * clsx로 조건부 클래스를 처리하고 twMerge로 중복 제거
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 날짜 포맷팅
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 밀리초를 초로 변환
 */
export function msToSeconds(ms: number): string {
  return (ms / 1000).toFixed(1);
}
