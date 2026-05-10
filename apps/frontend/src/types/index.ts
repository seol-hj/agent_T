/**
 * 타입 정의
 * 백엔드 Pydantic 스키마와 일치하도록 작성
 */

// Pipeline 관련 타입
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

// Scenario 관련 타입
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

// KPI 관련 타입
export interface KPIData {
  avg_travel_time: number;
  avg_waiting_time: number;
  throughput: number;
  completion_rate: number;
  congestion_index: number;
}

// Health Check
export interface HealthCheckResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
}
