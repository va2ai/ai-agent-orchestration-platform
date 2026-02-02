/**
 * Run Page V2 - Horizontal React Flow execution visualization.
 *
 * V2 Features:
 * - Horizontal layout (left to right)
 * - No agent nodes - agents embedded in iterations
 * - Support for agent row selection
 * - Side panel always shows useful content
 * - WebSocket for real-time updates
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
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
import SidePanel, { type Selection } from '../components/SidePanel';
import { getExecutionTrace, getRunStatus } from '../api';
import { buildGraph } from '../utils/graphBuilder';
import { useWebSocket } from '../hooks/useWebSocket';
import type { ExecutionTrace, WebSocketEvent } from '../types';

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const flowContainerRef = useRef<HTMLDivElement>(null);

  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load execution trace
  const loadTrace = useCallback(async () => {
    if (!runId) return;

    try {
      const data = await getExecutionTrace(runId);
      setTrace(data);

      // Build graph from trace (V2: horizontal, no agent nodes)
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

  // Handle agent row click events from IterationNode
  useEffect(() => {
    const handleAgentRowClick = (e: Event) => {
      const customEvent = e as CustomEvent<{
        nodeId: string;
        agentIndex: number;
        iterationIndex: number;
      }>;

      setSelection({
        type: 'agent',
        nodeId: customEvent.detail.nodeId,
        nodeType: 'iteration',
        agentIndex: customEvent.detail.agentIndex,
      });
    };

    const container = flowContainerRef.current;
    if (container) {
      container.addEventListener('agent-row-click', handleAgentRowClick);
    }

    return () => {
      if (container) {
        container.removeEventListener('agent-row-click', handleAgentRowClick);
      }
    };
  }, []);

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
      setSelection({
        type: 'node',
        nodeId: node.id,
        nodeType: node.type || 'unknown',
      });
    },
    []
  );

  // Clear selection (show default summary)
  const clearSelection = useCallback(() => {
    setSelection(null);
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
      fitView: true,
      fitViewOptions: {
        padding: 0.2,
        maxZoom: 1.5,
      },
    }),
    []
  );

  // MiniMap node colors
  const getNodeColor = useCallback((node: Node) => {
    switch (node.type) {
      case 'input':
        return '#3b82f6'; // Blue
      case 'iteration':
        return '#8b5cf6'; // Purple
      case 'convergence':
        return '#f59e0b'; // Orange
      default:
        return '#6b7280'; // Gray
    }
  }, []);

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
    <div className="run-page run-page-v2">
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

      <div className="run-content run-content-v2">
        <div className="flow-container flow-container-v2" ref={flowContainerRef}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={clearSelection}
            nodeTypes={nodeTypes as NodeTypes}
            {...flowOptions}
          >
            <Background />
            <Controls showInteractive={false} />
            <MiniMap
              nodeStrokeWidth={3}
              nodeColor={getNodeColor}
              zoomable
              pannable
            />
          </ReactFlow>
        </div>

        <SidePanel
          selection={selection}
          nodes={nodes}
          trace={trace}
          onClose={clearSelection}
        />
      </div>

      {/* Summary footer */}
      {trace && trace.status === 'completed' && (
        <footer className="run-footer run-footer-v2">
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
