/**
 * Iteration Node V2 - Container card with embedded agent summaries.
 *
 * V2 Design (from PRD):
 * - Iterations are PRIMARY nodes (not agents)
 * - Agent summaries shown as rows inside the node
 * - Severity badges (🔴 High, 🟡 Medium, 🟢 Low)
 * - Compact display for scanability
 * - Clicking agent rows triggers selection for detailed inspection
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { IterationNodeData, AgentSummary } from '../../types';

interface IterationNodeProps {
  data: IterationNodeData;
  id: string;
}

function IterationNode({ data, id }: IterationNodeProps) {
  const hasHighIssues = data.highIssueCount > 0;
  const agents = (data.agents || []) as AgentSummary[];

  // Handle agent row click - dispatch custom event for parent to handle
  const handleAgentClick = (agentIndex: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const event = new CustomEvent('agent-row-click', {
      bubbles: true,
      detail: { nodeId: id, agentIndex, iterationIndex: data.iterationIndex },
    });
    (e.target as HTMLElement).dispatchEvent(event);
  };

  return (
    <div className={`iteration-node-v2 ${hasHighIssues ? 'has-high-issues' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />

      {/* Header */}
      <div className="iteration-header">
        <span className="iteration-number">Iteration {data.iterationIndex}</span>
        {data.delta > 0 && (
          <span className="iteration-delta">{(data.delta * 100).toFixed(0)}% Δ</span>
        )}
      </div>

      {/* Issue Summary - Compact badges */}
      <div className="issue-badges">
        {data.highIssueCount > 0 && (
          <span className="badge badge-high">{data.highIssueCount} high</span>
        )}
        {data.mediumIssueCount > 0 && (
          <span className="badge badge-medium">{data.mediumIssueCount} med</span>
        )}
        {data.lowIssueCount > 0 && (
          <span className="badge badge-low">{data.lowIssueCount} low</span>
        )}
        {data.issueCount === 0 && (
          <span className="badge badge-success">No issues</span>
        )}
      </div>

      {/* Agent Summaries - Embedded rows */}
      {agents.length > 0 && (
        <div className="agent-summaries">
          {agents.map((agent, idx) => (
            <div
              key={idx}
              className={`agent-row ${agent.highIssues > 0 ? 'has-high' : ''}`}
              onClick={(e) => handleAgentClick(idx, e)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleAgentClick(idx, e as unknown as React.MouseEvent);
                }
              }}
            >
              <span className="agent-icon">🤖</span>
              <span className="agent-name">{agent.name || `Agent ${String.fromCharCode(65 + idx)}`}</span>
              <span className="agent-issues">
                {agent.issues} issue{agent.issues !== 1 ? 's' : ''}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default memo(IterationNode);
