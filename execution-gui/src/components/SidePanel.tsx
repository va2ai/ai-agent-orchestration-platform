/**
 * Side Panel V2 - Always useful inspection pane.
 *
 * V2 Requirements (from PRD):
 * - Default state: run summary with instructions (not "Click a node...")
 * - Iteration: show delta, issues by severity, per-agent contributions
 * - Agent row: issues from that agent, notes, assessment
 * - Convergence: stop rule, delta metrics, high-severity remaining, config
 * - Never show "Unknown" - use fallback labels
 */

import type { Node } from '@xyflow/react';
import type {
  InputNodeData,
  IterationNodeData,
  ConvergenceNodeData,
  ExecutionIssue,
  ExecutionTrace,
  AgentSummary,
} from '../types';

// Selection can be a node or a specific agent row
export interface Selection {
  type: 'node' | 'agent';
  nodeId: string;
  nodeType: string;
  agentIndex?: number;
}

interface SidePanelProps {
  selection: Selection | null;
  nodes: Node[];
  trace: ExecutionTrace | null;
  onClose: () => void;
}

export default function SidePanel({ selection, nodes, trace, onClose }: SidePanelProps) {
  // Default state: show run summary when nothing selected
  if (!selection || !trace) {
    return (
      <div className="side-panel default-state">
        <div className="panel-header">
          <h3>Run Summary</h3>
        </div>
        <div className="panel-content">
          {trace ? (
            <RunSummary trace={trace} />
          ) : (
            <div className="empty-state">
              <p>Loading execution data...</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Find the selected node
  const selectedNode = nodes.find((n) => n.id === selection.nodeId);
  if (!selectedNode) {
    return (
      <div className="side-panel">
        <div className="panel-header">
          <h3>Details</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        <div className="panel-content">
          <RunSummary trace={trace} />
        </div>
      </div>
    );
  }

  const renderContent = () => {
    // Handle agent row selection within iteration node
    if (selection.type === 'agent' && selectedNode.type === 'iteration') {
      const iterData = selectedNode.data as unknown as IterationNodeData;
      const agent = iterData.agents[selection.agentIndex ?? 0];
      if (agent) {
        return <AgentRowDetails agent={agent} />;
      }
    }

    // Handle node-level selection
    switch (selectedNode.type) {
      case 'input':
        return <InputNodeDetails data={selectedNode.data as unknown as InputNodeData} />;
      case 'iteration': {
        const iterData = selectedNode.data as unknown as IterationNodeData;
        const iteration = trace.iterations.find(
          (it) => it.iteration_index === iterData.iterationIndex
        );
        return <IterationNodeDetails data={iterData} issues={iteration?.issues || []} />;
      }
      case 'convergence':
        return <ConvergenceNodeDetails data={selectedNode.data as unknown as ConvergenceNodeData} trace={trace} />;
      default:
        return <RunSummary trace={trace} />;
    }
  };

  const getTitle = () => {
    if (selection.type === 'agent') {
      const iterData = selectedNode.data as unknown as IterationNodeData;
      const agent = iterData.agents[selection.agentIndex ?? 0];
      return agent?.name || 'Agent Details';
    }
    switch (selectedNode.type) {
      case 'input':
        return 'Input Document';
      case 'iteration':
        return `Iteration ${(selectedNode.data as unknown as IterationNodeData).iterationIndex}`;
      case 'convergence':
        return 'Convergence';
      default:
        return 'Details';
    }
  };

  return (
    <div className="side-panel">
      <div className="panel-header">
        <h3>{getTitle()}</h3>
        <button className="close-button" onClick={onClose}>×</button>
      </div>
      <div className="panel-content">{renderContent()}</div>
    </div>
  );
}

/**
 * Default state: Run summary with key metrics
 */
function RunSummary({ trace }: { trace: ExecutionTrace }) {
  const getStopReasonLabel = () => {
    switch (trace.stopped_by) {
      case 'no_high_issues':
        return 'All high severity issues resolved';
      case 'max_iterations':
        return 'Maximum iterations reached';
      case 'delta_threshold':
        return 'Document stabilized';
      case 'custom':
        return 'Custom stop condition';
      default:
        return trace.convergence_reason || 'Run completed';
    }
  };

  return (
    <div className="run-summary">
      <div className="summary-section">
        <h4>📊 Overview</h4>
        <dl>
          <dt>Status</dt>
          <dd className={`status-badge ${trace.status}`}>{trace.status}</dd>
          <dt>Iterations</dt>
          <dd>{trace.total_iterations} / {trace.max_iterations}</dd>
          <dt>Document Growth</dt>
          <dd>{((trace.final_document_length / trace.initial_document_length - 1) * 100).toFixed(0)}%</dd>
        </dl>
      </div>

      {trace.status === 'completed' && (
        <div className="summary-section">
          <h4>🎯 Result</h4>
          <p className="stop-reason">{getStopReasonLabel()}</p>
        </div>
      )}

      <div className="summary-section">
        <h4>📋 Final Issues</h4>
        <div className="issue-summary-grid">
          <div className="issue-stat high">
            <span className="count">{trace.final_issue_counts.high}</span>
            <span className="label">High</span>
          </div>
          <div className="issue-stat medium">
            <span className="count">{trace.final_issue_counts.medium}</span>
            <span className="label">Medium</span>
          </div>
          <div className="issue-stat low">
            <span className="count">{trace.final_issue_counts.low}</span>
            <span className="label">Low</span>
          </div>
        </div>
      </div>

      <div className="summary-instruction">
        <p>Select an iteration to inspect diff and issue details.</p>
      </div>
    </div>
  );
}

/**
 * Input node details
 */
function InputNodeDetails({ data }: { data: InputNodeData }) {
  return (
    <div className="node-details input-details">
      <div className="detail-section">
        <h4>📄 Document</h4>
        <dl>
          <dt>Title</dt>
          <dd>{data.title || 'Untitled Document'}</dd>
          <dt>Length</dt>
          <dd>{data.documentLength.toLocaleString()} characters</dd>
        </dl>
      </div>
    </div>
  );
}

/**
 * Iteration node details - issues grouped by severity, per-agent contributions
 */
function IterationNodeDetails({
  data,
  issues,
}: {
  data: IterationNodeData;
  issues: ExecutionIssue[];
}) {
  // Group issues by severity
  const highIssues = issues.filter((i) => i.severity === 'high');
  const mediumIssues = issues.filter((i) => i.severity === 'medium');
  const lowIssues = issues.filter((i) => i.severity === 'low');

  return (
    <div className="node-details iteration-details">
      <div className="detail-section">
        <h4>📊 Metrics</h4>
        <dl>
          <dt>Total Issues</dt>
          <dd>{data.issueCount}</dd>
          <dt>Delta</dt>
          <dd>{data.delta > 0 ? `${(data.delta * 100).toFixed(1)}%` : 'N/A'}</dd>
        </dl>
      </div>

      {/* Issue counts by severity */}
      <div className="detail-section">
        <h4>🎯 Issues by Severity</h4>
        <div className="severity-breakdown">
          {data.highIssueCount > 0 && (
            <div className="severity-row high">
              <span className="severity-badge">HIGH</span>
              <span className="severity-count">{data.highIssueCount}</span>
            </div>
          )}
          {data.mediumIssueCount > 0 && (
            <div className="severity-row medium">
              <span className="severity-badge">MEDIUM</span>
              <span className="severity-count">{data.mediumIssueCount}</span>
            </div>
          )}
          {data.lowIssueCount > 0 && (
            <div className="severity-row low">
              <span className="severity-badge">LOW</span>
              <span className="severity-count">{data.lowIssueCount}</span>
            </div>
          )}
        </div>
      </div>

      {/* Per-agent contributions */}
      {data.agents && data.agents.length > 0 && (
        <div className="detail-section">
          <h4>🤖 Agent Contributions</h4>
          <div className="agent-contributions">
            {data.agents.map((agent, idx) => (
              <div key={idx} className={`agent-contrib ${agent.highIssues > 0 ? 'has-high' : ''}`}>
                <span className="agent-name">{agent.name || `Agent ${String.fromCharCode(65 + idx)}`}</span>
                <span className="agent-issues">
                  {agent.issues} issue{agent.issues !== 1 ? 's' : ''}
                  {agent.highIssues > 0 && (
                    <span className="high-badge"> ({agent.highIssues} high)</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issue list */}
      {issues.length > 0 && (
        <div className="detail-section">
          <h4>📝 Issue Details</h4>
          <div className="issues-list-v2">
            {highIssues.length > 0 && (
              <IssueGroup severity="high" issues={highIssues} />
            )}
            {mediumIssues.length > 0 && (
              <IssueGroup severity="medium" issues={mediumIssues} />
            )}
            {lowIssues.length > 0 && (
              <IssueGroup severity="low" issues={lowIssues} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Issue group component
 */
function IssueGroup({ severity, issues }: { severity: string; issues: ExecutionIssue[] }) {
  return (
    <div className={`issue-group ${severity}`}>
      {issues.map((issue, idx) => (
        <div key={idx} className="issue-item-v2">
          <span className="issue-message">{issue.message}</span>
          {issue.category && (
            <span className="issue-category">{issue.category}</span>
          )}
          {issue.suggested_fix && (
            <div className="issue-fix">
              <strong>Fix:</strong> {issue.suggested_fix}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/**
 * Agent row details - when clicking an agent within an iteration
 */
function AgentRowDetails({
  agent,
}: {
  agent: AgentSummary;
}) {
  return (
    <div className="node-details agent-row-details">
      <div className="detail-section">
        <h4>🤖 {agent.name || 'Agent'}</h4>
        {agent.role && <div className="agent-role">{agent.role}</div>}
        <dl>
          <dt>Issues Found</dt>
          <dd>{agent.issues}</dd>
          <dt>High Severity</dt>
          <dd className={agent.highIssues > 0 ? 'high' : ''}>
            {agent.highIssues}
          </dd>
        </dl>
      </div>

      {agent.assessment && (
        <div className="detail-section">
          <h4>📋 Assessment</h4>
          <p className="assessment-text">{agent.assessment}</p>
        </div>
      )}
    </div>
  );
}

/**
 * Convergence node details - stop rule, metrics, config
 */
function ConvergenceNodeDetails({
  data,
  trace,
}: {
  data: ConvergenceNodeData;
  trace: ExecutionTrace;
}) {
  const getStopLabel = () => {
    switch (data.stoppedBy) {
      case 'no_high_issues':
        return 'No High Severity Issues';
      case 'max_iterations':
        return 'Maximum Iterations Reached';
      case 'delta_threshold':
        return 'Document Stabilized';
      case 'custom':
        return 'Custom Stop Condition';
      default:
        return 'Process Stopped';
    }
  };

  return (
    <div className="node-details convergence-details-v2">
      <div className="detail-section">
        <h4>{data.converged ? '✅ Converged' : '⚠️ Stopped'}</h4>
        <dl>
          <dt>Stop Rule</dt>
          <dd>{getStopLabel()}</dd>
          <dt>Iterations</dt>
          <dd>{data.totalIterations} / {data.maxIterations}</dd>
        </dl>
      </div>

      <div className="detail-section">
        <h4>📊 Final Metrics</h4>
        <div className="final-metrics">
          <div className="metric-row">
            <span className="metric-label">High Issues</span>
            <span className={`metric-value ${data.finalHighCount > 0 ? 'high' : ''}`}>
              {data.finalHighCount}
            </span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Medium Issues</span>
            <span className="metric-value">{data.finalMediumCount}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Low Issues</span>
            <span className="metric-value">{data.finalLowCount}</span>
          </div>
        </div>
      </div>

      {data.reason && (
        <div className="detail-section">
          <h4>💬 Reason</h4>
          <p className="convergence-reason">{data.reason}</p>
        </div>
      )}

      <div className="detail-section">
        <h4>⚙️ Configuration</h4>
        <dl>
          <dt>Max Iterations</dt>
          <dd>{trace.max_iterations}</dd>
          <dt>Participants</dt>
          <dd>{trace.participants?.length || 'N/A'}</dd>
        </dl>
      </div>
    </div>
  );
}
