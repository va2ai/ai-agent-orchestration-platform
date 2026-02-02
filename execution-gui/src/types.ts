/**
 * Type definitions for the Execution Visualizer GUI.
 *
 * These types mirror the API response models and define the graph structure.
 */

export type IssueSeverity = 'high' | 'medium' | 'low';

export interface ExecutionIssue {
  severity: IssueSeverity;
  message: string;
  category?: string;
  suggested_fix?: string;
}

export interface AgentExecution {
  name: string;
  role?: string;
  issues: number;
  high_issues: number;
  notes?: string;
  assessment?: string;
}

export interface IterationExecution {
  iteration_index: number;
  delta: number;
  issues: ExecutionIssue[];
  issue_counts: {
    high: number;
    medium: number;
    low: number;
  };
  agents: AgentExecution[];
  document_version: number;
  document_length: number;
}

export interface Participant {
  name: string;
  role?: string;
  expertise?: string;
  perspective?: string;
  model?: string;
}

export interface ExecutionTrace {
  run_id: string;
  title: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  stopped_by?: 'no_high_issues' | 'max_iterations' | 'delta_threshold' | 'custom';
  convergence_reason?: string;
  initial_document_length: number;
  final_document_length: number;
  iterations: IterationExecution[];
  total_iterations: number;
  max_iterations: number;
  participants: Participant[];
  moderator_focus?: string;
  total_issues_identified: number;
  final_issue_counts: {
    high: number;
    medium: number;
    low: number;
  };
  started_at?: string;
  completed_at?: string;
}

// Node data types for React Flow - use Record<string, unknown> compatible types
export type InputNodeData = Record<string, unknown> & {
  label: string;
  documentLength: number;
  title: string;
};

export type IterationNodeData = Record<string, unknown> & {
  label: string;
  iterationIndex: number;
  issueCount: number;
  highIssueCount: number;
  delta: number;
};

export type AgentNodeData = Record<string, unknown> & {
  label: string;
  name: string;
  role?: string;
  issues: number;
  highIssues: number;
  assessment?: string;
};

export type ConvergenceNodeData = Record<string, unknown> & {
  label: string;
  stoppedBy: string;
  reason: string;
  converged: boolean;
};

// API types
export interface RunListItem {
  run_id: string;
  title: string;
  created_at?: string;
  status: string;
  iterations: number;
  converged: boolean;
}

export interface StartOrchestrationRequest {
  document: string;
  title: string;
  max_iterations: number;
  document_type: string;
  num_participants: number;
  model: string;
  goal?: string;
  participant_style?: string;
}

export interface StartOrchestrationResponse {
  run_id: string;
  status: string;
  websocket_url: string;
}

// WebSocket event types
export type WebSocketEventType =
  | 'session_created'
  | 'roundtable_generated'
  | 'iteration_start'
  | 'critic_review_start'
  | 'critic_review_complete'
  | 'convergence_check'
  | 'moderator_start'
  | 'moderator_complete'
  | 'refinement_complete'
  | 'log';

export interface WebSocketEvent {
  type: WebSocketEventType;
  data: Record<string, unknown>;
  timestamp: string;
}
