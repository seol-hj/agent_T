import type { PipelineExecutionRequest, PipelineExecutionResult, HealthCheckResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

/**
 * API Client
 * 백엔드 REST API와 통신
 */
class APIClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  /**
   * 공통 fetch 래퍼
   */
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
      const error = await response.json().catch(() => ({ 
        detail: `HTTP ${response.status}: ${response.statusText}` 
      }));
      throw new Error(error.detail || `Request failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Health Check
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request('/health');
  }

  /**
   * Pipeline 실행
   */
  async runPipeline(request: PipelineExecutionRequest): Promise<PipelineExecutionResult> {
    return this.request('/pipeline/run', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Pipeline 진행률 조회
   */
  async getPipelineProgress(executionId: string): Promise<PipelineExecutionResult> {
    return this.request(`/pipeline/${executionId}/status`);
  }

  /**
   * Orchestrator - 자연어 파싱
   */
  async parseUserRequest(userRequest: string) {
    return this.request('/orchestrator/parse', {
      method: 'POST',
      body: JSON.stringify({ user_request: userRequest }),
    });
  }

  /**
   * Scenario Builder
   */
  async buildScenario(request: any) {
    return this.request('/scenario/build', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

export const apiClient = new APIClient(API_BASE_URL);
