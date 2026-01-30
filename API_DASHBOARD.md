# PRD Refinement API + Dashboard

## Overview

Web-based API and real-time dashboard for automated PRD quality improvement. Built with FastAPI and vanilla JavaScript.

## Architecture

- **Backend**: FastAPI with async orchestration
- **Frontend**: HTML + Vanilla JS + Tailwind CSS
- **Real-time**: WebSocket for live progress updates
- **Storage**: JSON file-based (same as CLI)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start API Server

```bash
python run_api.py
```

The server will start on http://localhost:8000

### 3. Access Dashboard

Open your browser to:
- **Dashboard**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs (interactive OpenAPI documentation)

## Features

### Dashboard Features

1. **Start Refinement**
   - Input PRD title and content
   - Set max iterations (1-10)
   - Click "Start Refinement"

2. **Real-time Progress**
   - Live iteration updates
   - Critic review progress
   - Issue counts (High/Medium)
   - Token usage tracking
   - Activity log

3. **Results**
   - Rendered markdown PRD
   - View reviews
   - View convergence report

4. **Session History**
   - List recent sessions
   - Click to load past PRDs
   - See convergence status

### API Endpoints

#### Sessions

- `GET /api/sessions/` - List all sessions
- `GET /api/sessions/{session_id}` - Get session details
- `GET /api/sessions/{session_id}/prd/{version}` - Get PRD version
- `GET /api/sessions/{session_id}/reviews/{version}` - Get reviews
- `GET /api/sessions/{session_id}/report` - Get convergence report

#### Refinement

- `POST /api/refinement/start` - Start refinement
  ```json
  {
    "title": "Feature X",
    "content": "# Feature\n\nDescription...",
    "max_iterations": 3
  }
  ```
- `GET /api/refinement/status/{session_id}` - Get status

#### WebSocket

- `WS /ws/refinement/{session_id}` - Real-time updates

### WebSocket Events

The WebSocket connection sends the following event types:

1. **session_created**
   ```json
   {
     "type": "session_created",
     "data": {"session_id": "session_20260129_120000"},
     "timestamp": "2026-01-29T12:00:00.000Z"
   }
   ```

2. **iteration_start**
   ```json
   {
     "type": "iteration_start",
     "data": {"iteration": 1, "max_iterations": 3},
     "timestamp": "..."
   }
   ```

3. **critic_review_start**
   ```json
   {
     "type": "critic_review_start",
     "data": {"critic": "prd_critic"},
     "timestamp": "..."
   }
   ```

4. **critic_review_complete**
   ```json
   {
     "type": "critic_review_complete",
     "data": {
       "critic": "prd_critic",
       "issues_count": 10,
       "high_count": 3,
       "tokens": {"total_tokens": 1500}
     },
     "timestamp": "..."
   }
   ```

5. **convergence_check**
   ```json
   {
     "type": "convergence_check",
     "data": {
       "converged": false,
       "reason": "5 high severity issues remaining",
       "iteration": 1
     },
     "timestamp": "..."
   }
   ```

6. **moderator_start** / **moderator_complete**
   ```json
   {
     "type": "moderator_complete",
     "data": {
       "new_version": 2,
       "tokens": {"total_tokens": 2000}
     },
     "timestamp": "..."
   }
   ```

7. **refinement_complete**
   ```json
   {
     "type": "refinement_complete",
     "data": {
       "final_version": 3,
       "report": {...}
     },
     "timestamp": "..."
   }
   ```

## File Structure

```
round/
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routes/
│   │   ├── sessions.py         # Session CRUD
│   │   ├── refinement.py       # Start/status endpoints
│   │   └── websocket.py        # WebSocket handler
│   ├── models/
│   │   └── api_models.py       # Request/response models
│   └── services/
│       └── async_orchestrator.py  # Async refinement
├── ui/
│   ├── index.html              # Dashboard
│   └── static/
│       ├── css/
│       │   └── styles.css
│       └── js/
│           ├── app.js          # Main logic
│           ├── websocket.js    # WebSocket client
│           └── visualization.js # Progress display
├── run_api.py                  # Server startup script
└── main.py                     # CLI (still available)
```

## Usage Examples

### Example 1: Start Refinement via API

```bash
curl -X POST http://localhost:8000/api/refinement/start \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AI Chatbot",
    "content": "# AI Chatbot\n\nBuild a chatbot...",
    "max_iterations": 3
  }'
```

Response:
```json
{
  "session_id": "session_20260129_120000",
  "status": "started"
}
```

### Example 2: Get Status

```bash
curl http://localhost:8000/api/refinement/status/session_20260129_120000
```

### Example 3: List Sessions

```bash
curl http://localhost:8000/api/sessions/
```

### Example 4: Get Final PRD

```bash
curl http://localhost:8000/api/sessions/session_20260129_120000/prd/3
```

## Performance

### Async Improvements

The async orchestrator runs critics in parallel:

- **Sync (CLI)**: ~4 minutes for 3 iterations
- **Async (API)**: ~2-3 minutes for 3 iterations (up to 3x faster per iteration)

### Token Usage

Average for 3 iterations:
- PRD Critic: ~5K tokens
- Engineering Critic: ~5K tokens
- AI Risk Critic: ~5K tokens
- Moderator: ~9K tokens (3 iterations)
- **Total**: ~24K tokens

## Development

### Run in Development Mode

```bash
python run_api.py
```

Auto-reload is enabled for code changes.

### Run in Production

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing Endpoints

Use the interactive API docs at http://localhost:8000/docs to test endpoints directly in your browser.

## CLI Still Available

The original CLI remains fully functional:

```bash
python main.py --input test_prd.md --title "Test" --max-iterations 3
```

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Requires WebSocket support

## Security Notes

For production deployment:

1. Add authentication (JWT tokens)
2. Enable HTTPS/WSS
3. Configure CORS properly
4. Rate limit refinement endpoint
5. Validate content length
6. Use Redis for session state

## Troubleshooting

### Server won't start

Check that port 8000 is available:
```bash
netstat -ano | findstr :8000
```

### WebSocket connection fails

Ensure server is running and accessible. Check browser console for errors.

### Session not found

Sessions are stored in `data/prds/`. Ensure the directory exists and has correct permissions.

## Future Enhancements

1. **Database**: PostgreSQL for session metadata
2. **Authentication**: OAuth2/JWT
3. **Export**: PDF/Notion/Confluence
4. **Templates**: PRD starter templates
5. **Collaboration**: Multi-user sessions
6. **Analytics**: Metrics dashboard

## Support

For issues or questions:
- Check logs in `data/prds/{session_id}/refinement.log`
- Review API docs at http://localhost:8000/docs
- Check WebSocket events in browser console
