/**
 * API service for the Execution Visualizer.
 */

import type {
  ExecutionTrace,
  RunListItem,
  StartOrchestrationRequest,
  StartOrchestrationResponse,
} from './types';

const API_BASE = '/api/execution';

export async function listRuns(): Promise<{ runs: RunListItem[]; total: number }> {
  const response = await fetch(`${API_BASE}/runs`);
  if (!response.ok) {
    throw new Error(`Failed to list runs: ${response.statusText}`);
  }
  return response.json();
}

export async function getExecutionTrace(runId: string): Promise<ExecutionTrace> {
  const response = await fetch(`${API_BASE}/trace/${runId}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Run not found');
    }
    throw new Error(`Failed to get execution trace: ${response.statusText}`);
  }
  return response.json();
}

export async function startOrchestration(
  request: StartOrchestrationRequest
): Promise<StartOrchestrationResponse> {
  const response = await fetch(`${API_BASE}/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Failed to start orchestration: ${response.statusText}`);
  }
  return response.json();
}

export async function getRunStatus(
  runId: string
): Promise<{ run_id: string; status: string; current_iteration: number; max_iterations: number }> {
  const response = await fetch(`${API_BASE}/status/${runId}`);
  if (!response.ok) {
    throw new Error(`Failed to get run status: ${response.statusText}`);
  }
  return response.json();
}

export interface DocumentTypeDetectionResult {
  document_type: string;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

export async function detectDocumentType(content: string): Promise<DocumentTypeDetectionResult> {
  const response = await fetch(`${API_BASE}/detect-document-type`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });
  if (!response.ok) {
    throw new Error(`Failed to detect document type: ${response.statusText}`);
  }
  return response.json();
}
