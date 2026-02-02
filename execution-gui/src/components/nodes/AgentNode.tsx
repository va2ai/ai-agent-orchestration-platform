/**
 * Agent Node - Represents a single agent's contribution in an iteration.
 *
 * Displays:
 * - Agent name
 * - Role
 * - Issue count
 * - High severity indicator
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { AgentNodeData } from '../../types';

interface AgentNodeProps {
  data: AgentNodeData;
}

function AgentNode({ data }: AgentNodeProps) {
  const hasHighIssues = data.highIssues > 0;

  return (
    <div className={`agent-node ${hasHighIssues ? 'has-high-issues' : ''}`}>
      <Handle type="target" position={Position.Left} />

      <div className="node-icon">🤖</div>
      <div className="node-title">{data.name}</div>
      <div className="node-content">
        {data.role && <div className="node-role">{data.role}</div>}
        <div className="node-stat">
          <span className="stat-label">Issues:</span>
          <span className="stat-value">{data.issues}</span>
        </div>
        {hasHighIssues && (
          <div className="node-badge high">
            {data.highIssues} high severity
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(AgentNode);
