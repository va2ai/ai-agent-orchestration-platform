/**
 * Side Panel - Node details inspector.
 *
 * Shows detailed information when a node is selected:
 * - Node type and basic info
 * - Issues list (for iteration/agent nodes)
 * - Assessment text
 * - Convergence details
 */

import type { Node } from '@xyflow/react';
import type {
  InputNodeData,
  IterationNodeData,
  AgentNodeData,
  ConvergenceNodeData,
  ExecutionIssue,
} from '../types';

interface SidePanelProps {
  selectedNode: Node | null;
  issues?: ExecutionIssue[];
  onClose: () => void;
}

export default function SidePanel({ selectedNode, issues = [], onClose }: SidePanelProps) {
  if (!selectedNode) {
    return (
      <div className="side-panel empty">
        <p>Click a node to inspect details</p>
      </div>
    );
  }

  const renderContent = () => {
    const data = selectedNode.data as Record<string, unknown>;
    switch (selectedNode.type) {
      case 'input':
        return <InputNodeDetails data={data as unknown as InputNodeData} />;
      case 'iteration':
        return <IterationNodeDetails data={data as unknown as IterationNodeData} issues={issues} />;
      case 'agent':
        return <AgentNodeDetails data={data as unknown as AgentNodeData} />;
      case 'convergence':
        return <ConvergenceNodeDetails data={data as unknown as ConvergenceNodeData} />;
      default:
        return <p>Unknown node type</p>;
    }
  };

  return (
    <div className="side-panel">
      <div className="panel-header">
        <h3>Node Details</h3>
        <button className="close-button" onClick={onClose}>
          ×
        </button>
      </div>
      <div className="panel-content">{renderContent()}</div>
    </div>
  );
}

function InputNodeDetails({ data }: { data: InputNodeData }) {
  return (
    <div className="node-details input-details">
      <div className="detail-section">
        <h4>📄 Input Document</h4>
        <dl>
          <dt>Title</dt>
          <dd>{data.title || 'Untitled'}</dd>
          <dt>Length</dt>
          <dd>{data.documentLength.toLocaleString()} characters</dd>
        </dl>
      </div>
    </div>
  );
}

function IterationNodeDetails({
  data,
  issues,
}: {
  data: IterationNodeData;
  issues: ExecutionIssue[];
}) {
  return (
    <div className="node-details iteration-details">
      <div className="detail-section">
        <h4>🔁 Iteration {data.iterationIndex}</h4>
        <dl>
          <dt>Total Issues</dt>
          <dd>{data.issueCount}</dd>
          <dt>High Severity</dt>
          <dd className={data.highIssueCount > 0 ? 'high' : ''}>
            {data.highIssueCount}
          </dd>
          {data.delta > 0 && (
            <>
              <dt>Document Delta</dt>
              <dd>{(data.delta * 100).toFixed(1)}%</dd>
            </>
          )}
        </dl>
      </div>

      {issues.length > 0 && (
        <div className="detail-section">
          <h4>Issues</h4>
          <ul className="issues-list">
            {issues.map((issue, idx) => (
              <li key={idx} className={`issue-item ${issue.severity}`}>
                <span className="issue-severity">{issue.severity.toUpperCase()}</span>
                <span className="issue-message">{issue.message}</span>
                {issue.category && (
                  <span className="issue-category">{issue.category}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function AgentNodeDetails({ data }: { data: AgentNodeData }) {
  return (
    <div className="node-details agent-details">
      <div className="detail-section">
        <h4>🤖 {data.name}</h4>
        {data.role && (
          <div className="agent-role">{data.role}</div>
        )}
        <dl>
          <dt>Issues Found</dt>
          <dd>{data.issues}</dd>
          <dt>High Severity</dt>
          <dd className={data.highIssues > 0 ? 'high' : ''}>
            {data.highIssues}
          </dd>
        </dl>
      </div>

      {data.assessment && (
        <div className="detail-section">
          <h4>Assessment</h4>
          <p className="assessment-text">{data.assessment}</p>
        </div>
      )}
    </div>
  );
}

function ConvergenceNodeDetails({ data }: { data: ConvergenceNodeData }) {
  const getStopLabel = () => {
    switch (data.stoppedBy) {
      case 'no_high_issues':
        return 'No High Severity Issues';
      case 'max_iterations':
        return 'Maximum Iterations Reached';
      case 'delta_threshold':
        return 'Document Stable';
      case 'custom':
        return 'Custom Stop Condition';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="node-details convergence-details">
      <div className="detail-section">
        <h4>{data.converged ? '✅ Converged' : '⚠️ Stopped'}</h4>
        <dl>
          <dt>Stop Condition</dt>
          <dd>{getStopLabel()}</dd>
        </dl>
      </div>

      <div className="detail-section">
        <h4>Reason</h4>
        <p className="convergence-reason">{data.reason}</p>
      </div>
    </div>
  );
}
