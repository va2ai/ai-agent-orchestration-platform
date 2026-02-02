/**
 * Convergence Node V2 - Terminal state with enhanced context.
 *
 * V2 Design:
 * - Horizontal flow (handle on left)
 * - Clear stop reason display
 * - Issue count summary
 * - Never show "Unknown" - use fallback labels
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { ConvergenceNodeData } from '../../types';

interface ConvergenceNodeProps {
  data: ConvergenceNodeData;
}

function ConvergenceNode({ data }: ConvergenceNodeProps) {
  const getStopLabel = () => {
    switch (data.stoppedBy) {
      case 'no_high_issues':
        return 'Converged';
      case 'max_iterations':
        return 'Max Iterations';
      case 'delta_threshold':
        return 'Stabilized';
      case 'custom':
        return 'Custom Stop';
      default:
        return 'Stopped';
    }
  };

  const getIcon = () => {
    if (data.converged && data.stoppedBy === 'no_high_issues') {
      return '✅';
    }
    if (data.stoppedBy === 'max_iterations') {
      return '⚠️';
    }
    if (data.stoppedBy === 'delta_threshold') {
      return '📊';
    }
    return '🛑';
  };

  // Compact iteration display
  const iterationDisplay = `${data.totalIterations || 0}/${data.maxIterations || '?'}`;

  return (
    <div className={`convergence-node-v2 ${data.converged ? 'converged' : 'not-converged'}`}>
      <Handle type="target" position={Position.Left} />

      <div className="node-icon">{getIcon()}</div>
      <div className="node-title">{getStopLabel()}</div>

      <div className="convergence-stats">
        <span className="iteration-count">{iterationDisplay} iters</span>
      </div>

      {/* Final issue summary */}
      {(data.finalHighCount > 0 || data.finalMediumCount > 0 || data.finalLowCount > 0) && (
        <div className="final-issues">
          {data.finalHighCount > 0 && (
            <span className="badge badge-high">{data.finalHighCount}</span>
          )}
          {data.finalMediumCount > 0 && (
            <span className="badge badge-medium">{data.finalMediumCount}</span>
          )}
          {data.finalLowCount > 0 && (
            <span className="badge badge-low">{data.finalLowCount}</span>
          )}
        </div>
      )}
    </div>
  );
}

export default memo(ConvergenceNode);
