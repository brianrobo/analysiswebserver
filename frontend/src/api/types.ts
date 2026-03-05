// TypeScript types mirroring backend Pydantic schemas

export type UserRole = 'admin' | 'team_lead' | 'member' | 'viewer'
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
export type Theme = 'light' | 'dark'

// Auth
export interface User {
  id: number
  email: string
  full_name: string | null
  role: UserRole
  team_id: number | null
  is_active: boolean
  created_at: string
  last_login: string | null
}

export interface Token {
  access_token: string
  token_type: string
}

// Settings
export interface UserSettings {
  id: number
  user_id: number
  theme: Theme
  sidebar_collapsed: boolean
  open_tabs: string[]
  active_tab: string | null
  tool_preferences: Record<string, unknown>
  recent_tools: string[]
  created_at: string
  updated_at: string
}

export interface UserSettingsUpdate {
  theme?: Theme
  sidebar_collapsed?: boolean
  open_tabs?: string[]
  active_tab?: string | null
  tool_preferences?: Record<string, unknown>
  recent_tools?: string[]
}

// Analysis
export interface AnalysisJobResponse {
  id: number
  job_name: string
  status: JobStatus
  progress: number
  created_at: string
  error_message: string | null
  message: string | null
}

export interface AnalysisHistoryItem {
  id: number
  job_name: string
  status: JobStatus
  input_file: string | null
  created_at: string
}

export interface ImportInfo {
  module: string
  is_ui: boolean
}

export interface PureFunctionInfo {
  name: string
  line_number: number
  docstring: string | null
}

export interface FileAnalysis {
  file_path: string
  loc: number
  ui_ratio: number
  classification: 'ui' | 'logic' | 'mixed'
  pure_functions: PureFunctionInfo[]
  imports: ImportInfo[]
}

export interface ExtractionSuggestion {
  file_path: string
  function_name: string
  reason: string
}

export interface RefactoringSuggestion {
  file_path: string
  suggestion: string
  priority: 'high' | 'medium' | 'low'
}

export interface WebConversionGuide {
  steps: string[]
  estimated_effort: string
  recommended_framework: string
}

export interface AnalysisSummary {
  total_files: number
  total_loc: number
  ui_files: number
  logic_files: number
  mixed_files: number
  web_readiness_percent: number
  pure_functions_count: number
}

export interface ProjectAnalysisResult {
  project_name: string
  total_files: number
  total_loc: number
  file_analyses: FileAnalysis[]
  extraction_suggestions: ExtractionSuggestion[]
  refactoring_suggestions: RefactoringSuggestion[]
  web_conversion_guide: WebConversionGuide | null
  analysis_summary: AnalysisSummary
}

export interface AnalysisResultResponse {
  job_id: number
  job_name: string
  result_data: ProjectAnalysisResult
  summary: AnalysisSummary | null
  processing_time: number | null
  created_at: string
}

// Sharing
export interface ShareRequest {
  team_id: number
  can_view: boolean
  can_download: boolean
  expires_at: string | null
}

export interface ShareResponse {
  job_id: number
  team_id: number
  shared_by_user_id: number
  can_view: boolean
  can_download: boolean
  created_at: string
  expires_at: string | null
  message: string
}

export interface SharedAnalysisItem {
  job_id: number
  job_name: string | null
  status: JobStatus
  owner_id: number
  owner_name: string
  share: {
    can_view: boolean
    can_download: boolean
    shared_by_id: number
    shared_at: string
    expires_at: string | null
  }
  created_at: string
}

// WebSocket
export type WsMessageType = 'connected' | 'progress' | 'completed' | 'error' | 'ping'

export interface WsMessage {
  type: WsMessageType
  job_id?: number
  progress?: number
  status?: JobStatus
  message?: string
  summary?: AnalysisSummary
  error?: string
  timestamp?: string
}

// API error response
export interface ApiError {
  detail: string
}
