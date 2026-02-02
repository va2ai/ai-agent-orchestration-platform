/**
 * Input Node V2 - Initial document display.
 *
 * V2 Design:
 * - Horizontal flow (handle on right)
 * - Compact display
 * - Never show "Unknown" - use fallback labels
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { InputNodeData } from '../../types';

interface InputNodeProps {
  data: InputNodeData;
}

function InputNode({ data }: InputNodeProps) {
  // Format character count
  const formatLength = (length: number) => {
    if (length >= 1000) {
      return `${(length / 1000).toFixed(1)}K`;
    }
    return length.toString();
  };

  return (
    <div className="input-node-v2">
      <Handle type="source" position={Position.Right} />

      <div className="node-icon">📄</div>
      <div className="node-title">Input</div>
      <div className="node-content">
        <div className="input-title">{data.title || 'Untitled Document'}</div>
        <div className="input-length">{formatLength(data.documentLength)} chars</div>
      </div>
    </div>
  );
}

export default memo(InputNode);
