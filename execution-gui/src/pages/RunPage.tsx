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
  const [generatingStatus, setGeneratingStatus] = useState<{
    phase: 'loading' | 'generating' | 'ready';
    message: string;
    participants?: Array<{ name: string; role: string }>;
  }>({ phase: 'loading', message: 'Loading...' });

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

      // Handle generation phase events
      if (event.type === 'session_created') {
        setGeneratingStatus({
          phase: 'loading',
          message: 'Session created, preparing...',
        });
      } else if (event.type === 'roundtable_generating') {
        const data = event.data as { message?: string; num_participants?: number };
        setGeneratingStatus({
          phase: 'generating',
          message: data.message || `Generating ${data.num_participants || 3} expert participants...`,
        });
      } else if (event.type === 'roundtable_generated') {
        const data = event.data as { participants?: Array<{ name: string; role: string }> };
        setGeneratingStatus({
          phase: 'ready',
          message: 'Roundtable ready!',
          participants: data.participants,
        });
      }

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

  // WebSocket connection (connect for running or loading sessions)
  const shouldConnect = trace?.status === 'running' || (isLoading && runId);
  const { isConnected } = useWebSocket(
    shouldConnect ? runId ?? null : null,
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

  if (isLoading || (trace?.status === 'running' && generatingStatus.phase !== 'ready' && nodes.length === 0)) {
    return (
      <div className="run-page loading">
        <div className="generating-container">
          <div className="generating-animation">
            <div className="generating-circle"></div>
            <div className="generating-circle"></div>
            <div className="generating-circle"></div>
          </div>
          <h2 className="generating-title">
            {generatingStatus.phase === 'generating'
              ? 'Generating Roundtable'
              : 'Initializing...'}
          </h2>
          <p className="generating-message">{generatingStatus.message}</p>
          {generatingStatus.participants && (
            <div className="generated-participants">
              {generatingStatus.participants.map((p, i) => (
                <div key={i} className="participant-chip">
                  <span className="participant-icon">🤖</span>
                  <span className="participant-name">{p.name}</span>
                </div>
              ))}
            </div>
          )}
          {isConnected && (
            <div className="connection-status connected">
              <span className="status-dot"></span>
              Live connection
            </div>
          )}
        </div>
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
