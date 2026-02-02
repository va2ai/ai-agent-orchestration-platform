/**
 * Graph Builder - Converts ExecutionTrace to React Flow nodes and edges.
 *
 * Layout Rules (from PRD):
 * - Vertical flow (top → bottom)
 * - One column per iteration
 * - Agents laid out horizontally under iteration
 * - Convergence node always last
 * - No auto-layout engine - deterministic positions
 */

import type { Node, Edge } from '@xyflow/react';
import type { ExecutionTrace } from '../types';

// Layout constants
const VERTICAL_SPACING = 150;
const HORIZONTAL_SPACING = 200;
const AGENT_OFFSET_Y = 80;
const START_X = 400;
const START_Y = 50;

interface GraphResult {
  nodes: Node[];
  edges: Edge[];
}

export function buildGraph(trace: ExecutionTrace): GraphResult {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // 1. Input Node (always first)
  nodes.push({
    id: 'input',
    type: 'input',
    position: { x: START_X, y: START_Y },
    data: {
      label: 'Input Document',
      documentLength: trace.initial_document_length,
      title: trace.title,
    },
  });

  // Track current Y position
  let currentY = START_Y + VERTICAL_SPACING;

  // 2. Iteration Nodes
  trace.iterations.forEach((iteration, idx) => {
    const iterationId = `iteration-${iteration.iteration_index}`;

    // Calculate total issues
    const totalIssues = iteration.issue_counts.high +
      iteration.issue_counts.medium +
      iteration.issue_counts.low;

    nodes.push({
      id: iterationId,
      type: 'iteration',
      position: { x: START_X, y: currentY },
      data: {
        label: `Iteration ${iteration.iteration_index}`,
        iterationIndex: iteration.iteration_index,
        issueCount: totalIssues,
        highIssueCount: iteration.issue_counts.high,
        delta: iteration.delta,
      },
    });

    // Edge from previous node (input or previous iteration)
    const sourceId = idx === 0 ? 'input' : `iteration-${trace.iterations[idx - 1].iteration_index}`;
    edges.push({
      id: `edge-${sourceId}-${iterationId}`,
      source: sourceId,
      target: iterationId,
      sourceHandle: idx === 0 ? undefined : 'main',
      type: 'default',
      animated: trace.status === 'running',
    });

    // 3. Agent Nodes (horizontal layout under iteration)
    const agents = iteration.agents;
    const agentStartX = START_X - ((agents.length - 1) * HORIZONTAL_SPACING) / 2;

    agents.forEach((agent, agentIdx) => {
      const agentId = `agent-${iteration.iteration_index}-${agentIdx}`;

      nodes.push({
        id: agentId,
        type: 'agent',
        position: {
          x: agentStartX + agentIdx * HORIZONTAL_SPACING,
          y: currentY + AGENT_OFFSET_Y,
        },
        data: {
          label: agent.name,
          name: agent.name,
          role: agent.role,
          issues: agent.issues,
          highIssues: agent.high_issues,
          assessment: agent.assessment,
        },
      });

      // Edge from iteration to agent
      edges.push({
        id: `edge-${iterationId}-${agentId}`,
        source: iterationId,
        target: agentId,
        sourceHandle: 'agents',
        type: 'default',
        style: { strokeDasharray: '5,5' }, // Dashed for agent edges
      });
    });

    // Move Y down for next iteration
    currentY += VERTICAL_SPACING + (agents.length > 0 ? AGENT_OFFSET_Y + 50 : 0);
  });

  // 4. Convergence Node (always last, if run is completed)
  if (trace.status === 'completed' || trace.status === 'failed') {
    nodes.push({
      id: 'convergence',
      type: 'convergence',
      position: { x: START_X, y: currentY },
      data: {
        label: 'Convergence',
        stoppedBy: trace.stopped_by || 'unknown',
        reason: trace.convergence_reason || '',
        converged: trace.stopped_by === 'no_high_issues',
      },
    });

    // Edge from last iteration to convergence
    if (trace.iterations.length > 0) {
      const lastIteration = trace.iterations[trace.iterations.length - 1];
      edges.push({
        id: `edge-iteration-${lastIteration.iteration_index}-convergence`,
        source: `iteration-${lastIteration.iteration_index}`,
        target: 'convergence',
        sourceHandle: 'main',
        type: 'default',
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
