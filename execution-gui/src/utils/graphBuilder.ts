/**
 * Graph Builder V2 - Horizontal flow visualization.
 *
 * V2 Layout Requirements (from PRD):
 * - Horizontal flow (left → right)
 * - Only Input, Iteration, and Convergence nodes
 * - NO agent nodes - agents are embedded in iteration nodes
 * - Run fits in one viewport for up to ~5 iterations
 * - Severity badges, not extra nodes
 */

import type { Node, Edge } from '@xyflow/react';
import type { ExecutionTrace, AgentSummary } from '../types';

// V2 Layout constants - horizontal flow
const HORIZONTAL_SPACING = 280;  // Space between nodes (left to right)
const START_X = 50;              // Start position X
const START_Y = 200;             // Centered vertically

interface GraphResult {
  nodes: Node[];
  edges: Edge[];
}

export function buildGraph(trace: ExecutionTrace): GraphResult {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Track current X position for horizontal layout
  let currentX = START_X;

  // 1. Input Node (always first, on the left)
  nodes.push({
    id: 'input',
    type: 'input',
    position: { x: currentX, y: START_Y },
    data: {
      label: 'Input',
      documentLength: trace.initial_document_length,
      title: trace.title || 'Untitled Document',
    },
  });

  // Move right for next node
  currentX += HORIZONTAL_SPACING;

  // 2. Iteration Nodes - horizontal layout
  trace.iterations.forEach((iteration, idx) => {
    const iterationId = `iteration-${iteration.iteration_index}`;

    // Calculate issue counts
    const totalIssues = iteration.issue_counts.high +
      iteration.issue_counts.medium +
      iteration.issue_counts.low;

    // Transform agents to AgentSummary format
    const agentSummaries: AgentSummary[] = iteration.agents.map((agent, agentIdx) => ({
      name: agent.name || `Agent ${String.fromCharCode(65 + agentIdx)}`,  // Fallback: "Agent A", "Agent B", etc.
      role: agent.role,
      issues: agent.issues,
      highIssues: agent.high_issues,
      assessment: agent.assessment,
    }));

    nodes.push({
      id: iterationId,
      type: 'iteration',
      position: { x: currentX, y: START_Y },
      data: {
        label: `Iteration ${iteration.iteration_index}`,
        iterationIndex: iteration.iteration_index,
        issueCount: totalIssues,
        highIssueCount: iteration.issue_counts.high,
        mediumIssueCount: iteration.issue_counts.medium,
        lowIssueCount: iteration.issue_counts.low,
        delta: iteration.delta,
        agents: agentSummaries,
      },
    });

    // Edge from previous node (input or previous iteration)
    const sourceId = idx === 0 ? 'input' : `iteration-${trace.iterations[idx - 1].iteration_index}`;
    const hasHighIssues = idx > 0 && trace.iterations[idx - 1].issue_counts.high > 0;

    edges.push({
      id: `edge-${sourceId}-${iterationId}`,
      source: sourceId,
      target: iterationId,
      type: 'default',
      animated: trace.status === 'running',
      style: hasHighIssues ? { stroke: '#ef4444', strokeWidth: 2 } : undefined,
    });

    // Move right for next node
    currentX += HORIZONTAL_SPACING;
  });

  // 3. Convergence Node (always last, if run is completed or failed)
  if (trace.status === 'completed' || trace.status === 'failed') {
    const stoppedBy = trace.stopped_by || 'custom';
    const converged = stoppedBy === 'no_high_issues';

    // Build a proper reason string with fallback
    let reason = trace.convergence_reason || '';
    if (!reason) {
      switch (stoppedBy) {
        case 'no_high_issues':
          reason = 'All high severity issues resolved';
          break;
        case 'max_iterations':
          reason = `Reached maximum iterations (${trace.max_iterations})`;
          break;
        case 'delta_threshold':
          reason = 'Document stabilized below threshold';
          break;
        default:
          reason = 'Process completed';
      }
    }

    nodes.push({
      id: 'convergence',
      type: 'convergence',
      position: { x: currentX, y: START_Y },
      data: {
        label: converged ? 'Converged' : 'Stopped',
        stoppedBy: stoppedBy,
        reason: reason,
        converged: converged,
        totalIterations: trace.total_iterations,
        maxIterations: trace.max_iterations,
        finalHighCount: trace.final_issue_counts.high,
        finalMediumCount: trace.final_issue_counts.medium,
        finalLowCount: trace.final_issue_counts.low,
      },
    });

    // Edge from last iteration to convergence
    if (trace.iterations.length > 0) {
      const lastIteration = trace.iterations[trace.iterations.length - 1];
      const hasHighIssues = lastIteration.issue_counts.high > 0;

      edges.push({
        id: `edge-iteration-${lastIteration.iteration_index}-convergence`,
        source: `iteration-${lastIteration.iteration_index}`,
        target: 'convergence',
        type: 'default',
        style: hasHighIssues ? { stroke: '#ef4444', strokeWidth: 2 } : undefined,
      });
    } else {
      // Edge from input to convergence (no iterations)
      edges.push({
        id: 'edge-input-convergence',
        source: 'input',
        target: 'convergence',
        type: 'default',
      });
    }
  }

  return { nodes, edges };
}

/**
 * Get edge style based on issues.
 * Red for high issues, default gray otherwise.
 */
export function getEdgeStyle(hasHighIssues: boolean) {
  if (hasHighIssues) {
    return {
      stroke: '#ef4444', // Red for high issues
      strokeWidth: 2,
    };
  }
  return {
    stroke: '#6b7280', // Gray for normal
    strokeWidth: 1,
  };
}
