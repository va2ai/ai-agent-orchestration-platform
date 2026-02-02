/**
 * Custom node types for React Flow V2.
 *
 * V2 Changes:
 * - AgentNode removed (agents embedded in IterationNode)
 * - Only 3 node types: input, iteration, convergence
 * - Horizontal layout (handles on left/right instead of top/bottom)
 */

import InputNode from './InputNode';
import IterationNode from './IterationNode';
import ConvergenceNode from './ConvergenceNode';

// V2: Only 3 node types (no agent nodes)
export const nodeTypes = {
  input: InputNode,
  iteration: IterationNode,
  convergence: ConvergenceNode,
};

export { InputNode, IterationNode, ConvergenceNode };
