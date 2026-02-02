/**
 * Custom node types for React Flow.
 */

import InputNode from './InputNode';
import IterationNode from './IterationNode';
import AgentNode from './AgentNode';
import ConvergenceNode from './ConvergenceNode';

export const nodeTypes = {
  input: InputNode,
  iteration: IterationNode,
  agent: AgentNode,
  convergence: ConvergenceNode,
};

export { InputNode, IterationNode, AgentNode, ConvergenceNode };
