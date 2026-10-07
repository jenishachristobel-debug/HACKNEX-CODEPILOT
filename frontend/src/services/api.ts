import axios from 'axios';

export const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    if (config.headers) {
      if (typeof config.headers.delete === 'function') {
        config.headers.delete('Content-Type');
        config.headers.delete('content-type');
      }
      delete (config.headers as any)['Content-Type'];
      delete (config.headers as any)['content-type'];
    }
  }
  return config;
});

export const formatApiError = (
  err: any,
  fallbackMessage: string = 'Could not contact the repository upload service.'
): string => {
  // 1. Timeout error
  if (err.code === 'ECONNABORTED' || (err.message && err.message.toLowerCase().includes('timeout'))) {
    return 'Upload timed out. The repository may be too large or backend processing took too long.';
  }

  // 2. Backend unreachable / Network Error / 502 / 503 / Connection refused
  if (
    err.response?.status === 502 ||
    err.response?.status === 503 ||
    err.code === 'ECONNREFUSED' ||
    err.code === 'ERR_NETWORK' ||
    err.message === 'Network Error' ||
    (err.message && err.message.includes('502'))
  ) {
    return 'Backend service is unavailable. Make sure FastAPI is running on port 8000.';
  }

  // 3. Backend HTTP error with details
  if (err.response?.data?.detail) {
    const detail = err.response.data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((d: any) => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(', ');
    }
    if (typeof detail === 'object') {
      return JSON.stringify(detail);
    }
  }

  if (err.response?.data?.message) return err.response.data.message;
  if (err.message && !err.message.includes('status code') && err.message !== 'Network Error') {
    return err.message;
  }

  return fallbackMessage;
};

export interface HealthInfo {
  status: string;
  backend?: string;
  database: string;
  test_runner?: string;
  repository_scanner?: string;
  version: string;
  execution_mode: string;
  ai_provider: {
    configured: boolean;
    provider: string;
    model: string;
    mode?: string;
    fallback_enabled?: boolean;
    live_llm_status?: string;
    message: string;
  };
}

export interface SettingsStatus {
  execution_engine: string;
  reasoning_engine: string;
  max_repair_attempts: number;
  subprocess_timeout: number;
  max_upload_mb: number;
  human_approval_required: boolean;
  self_repair_in_sandbox: boolean;
  baseline_tests_enabled: boolean;
  regression_tests_enabled: boolean;
  post_patch_tests_enabled: boolean;
  stop_on_regression: boolean;
  archive_validation: boolean;
  path_traversal_protection: boolean;
  symlink_protection: boolean;
  secret_redaction: boolean;
  unsafe_command_blocking: boolean;
}

export interface BugReportInfo {
  has_bug_report: boolean;
  path: string;
  title: string;
  description: string;
  reproduction_command?: string;
  raw_content: string;
  suggested_task?: {
    bug_title: string;
    bug_description: string;
    reproduction_steps: string;
    expected_behavior: string;
    actual_behavior: string;
  };
}

export interface ProjectItem {
  id: number;
  name: string;
  description?: string;
  language: string;
  source_type: string;
  file_count: number;
  has_verified_fix?: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskItem {
  id: number;
  project_id: number;
  project_name?: string;
  bug_title: string;
  bug_description: string;
  error_traceback?: string;
  expected_behavior?: string;
  actual_behavior?: string;
  reproduction_steps?: string;
  mode: string;
  status: string;
  current_attempt: number;
  max_attempts: number;
  created_at: string;
  updated_at: string;
  latest_patch?: any;
  verification?: any;
}

export interface AnalysisData {
  id: number;
  task_id: number;
  summary: string;
  root_cause: string;
  affected_files: string[];
  affected_functions: string[];
  call_path?: string;
  evidence: string[];
  proposed_plan: string[];
  potential_side_effects: string[];
  uncertainties: string[];
  expected_behavior?: string;
  actual_behavior?: string;
  proposed_fix?: string;
  is_llm_generated: boolean;
  created_at?: string;
}

export interface PatchItem {
  id: number;
  task_id: number;
  attempt_number: number;
  target_file: string;
  original_code: string;
  new_code: string;
  diff: string;
  explanation?: string;
  potential_impact?: string;
  status: string;
  created_at: string;
}

export interface VerificationData {
  id: number;
  task_id: number;
  classification: string;
  functional_status: string;
  regression_status: string;
  syntax_status: string;
  security_status: string;
  evidence_summary: any;
  markdown_report: string;
  json_report: any;
  created_at: string;
}

export interface TestRunItem {
  id: number;
  attempt_number: number;
  stage: string;
  command: string;
  exit_code: number;
  duration_ms: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  output_log: string;
  test_details: Array<{
    name: string;
    status: string;
    duration_ms: number;
    message?: string;
  }>;
  created_at: string;
}

export interface HistoryItem {
  id: number;
  project_id?: number;
  project_name: string;
  bug_title: string;
  root_cause_summary?: string;
  target_file?: string;
  patch_summary?: string;
  outcome: string;
  created_at: string;
}

export const downloadCorrectedZip = async (projectId: number, projectName: string) => {
  const response = await api.get(`/projects/${projectId}/corrected-zip`, {
    responseType: 'blob'
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/zip' }));
  const link = document.createElement('a');
  link.href = url;
  const cleanName = (projectName || `project_${projectId}`).replace(/[^a-zA-Z0-9_-]/g, '_');
  link.setAttribute('download', `${cleanName}_corrected.zip`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const resetDemoProject = async () => {
  const response = await api.post('/projects/demo/reset');
  return response.data;
};

