/**
 * Input Node - Represents the initial document.
 *
 * Displays:
 * - Document icon
 * - Title
 * - Document length
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import type { InputNodeData } from '../../types';

interface InputNodeProps {
  data: InputNodeData;
}

function InputNode({ data }: InputNodeProps) {
  return (
    <div className="input-node">
      <Handle type="source" position={Position.Bottom} />
      <div className="node-icon">📄</div>
      <div className="node-title">Input Document</div>
      <div className="node-content">
        <div className="node-label">{data.title || 'Untitled'}</div>
        <div className="node-detail">Length: {data.documentLength.toLocaleString()} chars</div>
      </div>
    </div>
  );
}

export default memo(InputNode);
