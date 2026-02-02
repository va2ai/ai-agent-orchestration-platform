/**
 * AI Orchestrator - Execution Visualizer
 *
 * A read-only React Flow-based GUI for visualizing orchestration execution traces.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import InputPage from './pages/InputPage';
import RunPage from './pages/RunPage';
import './App.css';

function App() {
  return (
    <BrowserRouter basename="/visualizer">
      <Routes>
        <Route path="/" element={<InputPage />} />
        <Route path="/run/:runId" element={<RunPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
