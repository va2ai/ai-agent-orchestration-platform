/**
 * Convergence Node - Represents the terminal state of the run.
 *
 * Displays:
 * - Stop icon
 * - Convergence reason
 * - Whether it truly converged or hit max iterations
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
        return 'No High Issues';
      case 'max_iterations':
        return 'Max Iterations';
      case 'delta_threshold':
        return 'Stable Document';
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
    return '🛑';
  };

  return (
    <div className={`convergence-node ${data.converged ? 'converged' : 'not-converged'}`}>
      <Handle type="target" position={Position.Top} />

      <div className="node-icon">{getIcon()}</div>
      <div className="node-title">{getStopLabel()}</div>
      <div className="node-content">
        <div className="node-reason">{data.reason}</div>
      </div>
    </div>
  );
}

export default memo(ConvergenceNode);
