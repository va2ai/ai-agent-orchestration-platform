/**
 * Run Page - React Flow execution visualization.
 *
 * Features:
 * - Full-screen React Flow canvas
 * - Read-only (no drag handles, no editing)
 * - Side panel for node details
 * - WebSocket for real-time updates
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { nodeTypes } from '../components/nodes';
import SidePanel from '../components/SidePanel';
import { getExecutionTrace, getRunStatus } from '../api';
import { buildGraph } from '../utils/graphBuilder';
import { useWebSocket } from '../hooks/useWebSocket';
import type { ExecutionTrace, ExecutionIssue, WebSocketEvent } from '../types';

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedIssues, setSelectedIssues] = useState<ExecutionIssue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load execution trace
  const loadTrace = useCallback(async () => {
    if (!runId) return;

    try {
      const data = await getExecutionTrace(runId);
      setTrace(data);

      // Build graph from trace
      const { nodes: newNodes, edges: newEdges } = buildGraph(data);
      setNodes(newNodes);
      setEdges(newEdges);

      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trace');
    } finally {
      setIsLoading(false);
    }
  }, [runId, setNodes, setEdges]);

  // Initial load
  useEffect(() => {
    loadTrace();
  }, [loadTrace]);

  // Handle WebSocket events for real-time updates
  const handleWebSocketMessage = useCallback(
    (event: WebSocketEvent) => {
      console.log('WebSocket event:', event.type, event.data);

      // Reload trace on significant events
      if (
        event.type === 'iteration_start' ||
        event.type === 'critic_review_complete' ||
        event.type === 'refinement_complete'
      ) {
        loadTrace();
      }
    },
    [loadTrace]
  );

  // WebSocket connection (only for running sessions)
  const { isConnected } = useWebSocket(
    trace?.status === 'running' ? runId ?? null : null,
    {
      onMessage: handleWebSocketMessage,
    }
  );

  // Poll for status updates if WebSocket not connected
  useEffect(() => {
    if (!runId || trace?.status !== 'running' || isConnected) return;

    const interval = setInterval(async () => {
      try {
        const status = await getRunStatus(runId);
        if (status.status === 'completed' || status.status === 'failed') {
          loadTrace();
        }
      } catch {
        // Ignore polling errors
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [runId, trace?.status, isConnected, loadTrace]);

  // Handle node selection
  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      setSelectedNode(node);

      // Get issues for this node if it's an iteration
      if (node.type === 'iteration' && trace) {
        const iterationData = node.data as Record<string, unknown>;
        const iterationIndex = iterationData.iterationIndex as number;
        const iteration = trace.iterations.find(
          (it) => it.iteration_index === iterationIndex
        );
        setSelectedIssues(iteration?.issues || []);
      } else {
        setSelectedIssues([]);
      }
    },
    [trace]
  );

  // Clear selection
  const clearSelection = useCallback(() => {
    setSelectedNode(null);
    setSelectedIssues([]);
  }, []);

  // Memoize flow options for read-only mode
  const flowOptions = useMemo(
    () => ({
      nodesDraggable: false,
      nodesConnectable: false,
      elementsSelectable: true,
      zoomOnScroll: true,
      panOnScroll: true,
      panOnDrag: true,
    }),
    []
  );

  if (isLoading) {
    return (
      <div className="run-page loading">
        <div className="loading-spinner" />
        <p>Loading execution trace...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="run-page error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={() => navigate('/')}>Back to Home</button>
      </div>
    );
  }

  return (
    <div className="run-page">
      <header className="run-header">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back
        </button>
        <div className="run-info">
          <h1>{trace?.title || 'Untitled Run'}</h1>
          <div className="run-meta">
            <span className={`status ${trace?.status}`}>{trace?.status}</span>
            {trace?.status === 'running' && isConnected && (
              <span className="ws-status connected">Live</span>
            )}
            <span className="iterations">
              {trace?.total_iterations}/{trace?.max_iterations} iterations
            </span>
          </div>
        </div>
      </header>

      <div className="run-content">
        <div className="flow-container">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={clearSelection}
            nodeTypes={nodeTypes as NodeTypes}
            fitView
            {...flowOptions}
          >
            <Background />
            <Controls showInteractive={false} />
            <MiniMap
              nodeStrokeWidth={3}
              nodeColor={(node) => {
                switch (node.type) {
                  case 'input':
                    return '#3b82f6';
                  case 'iteration':
                    return '#8b5cf6';
                  case 'agent':
                    return '#10b981';
                  case 'convergence':
                    return '#f59e0b';
                  default:
                    return '#6b7280';
                }
              }}
            />
          </ReactFlow>
        </div>

        <SidePanel
          selectedNode={selectedNode}
          issues={selectedIssues}
          onClose={clearSelection}
        />
      </div>

      {/* Summary footer */}
      {trace && trace.status === 'completed' && (
        <footer className="run-footer">
          <div className="summary-stat">
            <span className="stat-label">Total Issues</span>
            <span className="stat-value">{trace.total_issues_identified}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">High</span>
            <span className="stat-value high">{trace.final_issue_counts.high}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Medium</span>
            <span className="stat-value medium">{trace.final_issue_counts.medium}</span>
          </div>
          <div className="summary-stat">
            <span className="stat-label">Low</span>
            <span className="stat-value low">{trace.final_issue_counts.low}</span>
          </div>
          {trace.convergence_reason && (
            <div className="summary-reason">
              {trace.convergence_reason}
            </div>
          )}
        </footer>
      )}
    </div>
  );
}
