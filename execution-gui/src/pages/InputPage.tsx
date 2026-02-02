/**
 * Input Page - Document input and orchestration start.
 *
 * Features:
 * - Textarea for document input
 * - Configuration options
 * - "Run Orchestration" button
 * - Recent runs list
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { startOrchestration, listRuns } from '../api';
import type { RunListItem } from '../types';

export default function InputPage() {
  const navigate = useNavigate();
  const [document, setDocument] = useState('');
  const [title, setTitle] = useState('');
  const [maxIterations, setMaxIterations] = useState(3);
  const [numParticipants, setNumParticipants] = useState(3);
  const [model, setModel] = useState('gpt-4-turbo');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentRuns, setRecentRuns] = useState<RunListItem[]>([]);

  useEffect(() => {
    loadRecentRuns();
  }, []);

  async function loadRecentRuns() {
    try {
      const { runs } = await listRuns();
      setRecentRuns(runs.slice(0, 10)); // Show last 10 runs
    } catch {
      // Ignore errors - runs list is optional
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!document.trim()) {
      setError('Please enter a document');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await startOrchestration({
        document,
        title: title || 'Untitled',
        max_iterations: maxIterations,
        document_type: 'document',
        num_participants: numParticipants,
        model,
      });

      // Navigate to run visualization
      navigate(`/run/${response.run_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start orchestration');
      setIsLoading(false);
    }
  }

  return (
    <div className="input-page">
      <header className="page-header">
        <h1>AI Orchestrator</h1>
        <p className="subtitle">Execution Visualizer</p>
      </header>

      <main className="page-content">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter document title..."
              className="input-field"
            />
          </div>

          <div className="form-group">
            <label htmlFor="document">Document</label>
            <textarea
              id="document"
              value={document}
              onChange={(e) => setDocument(e.target.value)}
              placeholder="Enter your document here..."
              className="document-textarea"
              rows={12}
            />
            <div className="char-count">{document.length.toLocaleString()} characters</div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="maxIterations">Max Iterations</label>
              <select
                id="maxIterations"
                value={maxIterations}
                onChange={(e) => setMaxIterations(Number(e.target.value))}
                className="input-field"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="numParticipants">Participants</label>
              <select
                id="numParticipants"
                value={numParticipants}
                onChange={(e) => setNumParticipants(Number(e.target.value))}
                className="input-field"
              >
                {[2, 3, 4, 5, 6].map((n) => (
                  <option key={n} value={n}>
                    {n} agents
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="model">Model</label>
              <select
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="input-field"
              >
                <optgroup label="OpenAI">
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                  <option value="gpt-4o">GPT-4o</option>
                  <option value="gpt-5.2">GPT-5.2</option>
                </optgroup>
                <optgroup label="Anthropic">
                  <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet</option>
                </optgroup>
                <optgroup label="Google">
                  <option value="gemini-3-pro-preview">Gemini 3 Pro</option>
                  <option value="gemini-3-flash-preview">Gemini 3 Flash</option>
                </optgroup>
              </select>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="submit-button" disabled={isLoading}>
            {isLoading ? 'Starting...' : 'Run Orchestration'}
          </button>
        </form>

        {recentRuns.length > 0 && (
          <aside className="recent-runs">
            <h2>Recent Runs</h2>
            <ul className="runs-list">
              {recentRuns.map((run) => (
                <li
                  key={run.run_id}
                  className="run-item"
                  onClick={() => navigate(`/run/${run.run_id}`)}
                >
                  <div className="run-title">{run.title || 'Untitled'}</div>
                  <div className="run-meta">
                    <span className={`run-status ${run.status}`}>{run.status}</span>
                    <span className="run-iterations">{run.iterations} iterations</span>
                    {run.converged && <span className="run-converged">Converged</span>}
                  </div>
                </li>
              ))}
            </ul>
          </aside>
        )}
      </main>
    </div>
  );
}
