/**
 * Iteration Node - Represents a single iteration of the refinement loop.
 *
 * Displays:
 * - Iteration number
 * - Issue summary (total, high severity)
 * - Document delta
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { IterationNodeData } from '../../types';

interface IterationNodeProps {
  data: IterationNodeData;
}

function IterationNode({ data }: IterationNodeProps) {
  const hasHighIssues = data.highIssueCount > 0;

  return (
    <div className={`iteration-node ${hasHighIssues ? 'has-high-issues' : ''}`}>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} id="main" />
      <Handle type="source" position={Position.Right} id="agents" />

      <div className="node-icon">🔁</div>
      <div className="node-title">Iteration {data.iterationIndex}</div>
      <div className="node-content">
        <div className="node-stat">
          <span className="stat-label">Issues:</span>
          <span className="stat-value">{data.issueCount}</span>
          {hasHighIssues && (
            <span className="stat-high">({data.highIssueCount} high)</span>
          )}
        </div>
        {data.delta > 0 && (
          <div className="node-stat">
            <span className="stat-label">Delta:</span>
            <span className="stat-value">{(data.delta * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(IterationNode);
