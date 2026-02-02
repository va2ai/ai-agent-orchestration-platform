import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Union
from ..models.prd_models import PRD, PRDReview
from ..models.document_models import Document, DocumentReview

class PRDStorage:
    """Handle PRD versioning and persistence"""

    def __init__(self, base_dir: str = "data/prds"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_dir / "prd_index.json"
        self._ensure_index()

    def _ensure_index(self):
        """Create index file if it doesn't exist"""
        if not self.index_file.exists():
            self.index_file.write_text(json.dumps({"sessions": []}, indent=2), encoding='utf-8')

    def create_session(self, title: str) -> str:
        """Create new PRD session and return session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Update index
        index_data = json.loads(self.index_file.read_text(encoding='utf-8'))
        index_data["sessions"].append({
            "session_id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "directory": str(session_dir)
        })
        self.index_file.write_text(json.dumps(index_data, indent=2), encoding='utf-8')

        return session_id

    def save_prd(self, session_id: str, prd: Union[PRD, Document]):
        """Save PRD/Document version to session directory"""
        session_dir = self.base_dir / session_id
        prd_file = session_dir / f"prd_v{prd.version}.json"
        prd_file.write_text(prd.model_dump_json(indent=2), encoding='utf-8')

    def save_reviews(self, session_id: str, version: int, reviews: List[Union[PRDReview, DocumentReview]]):
        """Save reviews for a PRD/Document version"""
        session_dir = self.base_dir / session_id
        reviews_file = session_dir / f"reviews_v{version}.json"
        reviews_data = [r.model_dump() for r in reviews]
        reviews_file.write_text(json.dumps(reviews_data, indent=2), encoding='utf-8')

    def save_roundtable_config(self, session_id: str, config: dict):
        """Save roundtable configuration (participants)"""
        session_dir = self.base_dir / session_id
        config_file = session_dir / "roundtable_config.json"
        config_file.write_text(json.dumps(config, indent=2), encoding='utf-8')

    def load_roundtable_config(self, session_id: str) -> Optional[dict]:
        """Load roundtable configuration"""
        session_dir = self.base_dir / session_id
        config_file = session_dir / "roundtable_config.json"
        if config_file.exists():
            return json.loads(config_file.read_text(encoding='utf-8'))
        return None

    def load_prd(self, session_id: str, version: int) -> PRD:
        """Load specific PRD version"""
        session_dir = self.base_dir / session_id
        prd_file = session_dir / f"prd_v{version}.json"
        prd_data = json.loads(prd_file.read_text(encoding='utf-8'))
        return PRD(**prd_data)

    def get_latest_version(self, session_id: str) -> int:
        """Get latest PRD version number for session"""
        session_dir = self.base_dir / session_id
        prd_files = list(session_dir.glob("prd_v*.json"))
        if not prd_files:
            return 0
        versions = [int(f.stem.split("_v")[1]) for f in prd_files]
        return max(versions)

    def save_convergence_report(self, session_id: str, report: dict):
        """Save convergence report"""
        session_dir = self.base_dir / session_id
        report_file = session_dir / "convergence_report.json"
        report_file.write_text(json.dumps(report, indent=2), encoding='utf-8')

    def list_sessions(self, limit: int = 50) -> List[dict]:
        """List all sessions with metadata"""
        index_data = json.loads(self.index_file.read_text(encoding='utf-8'))
        sessions = index_data.get("sessions", [])
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)[:limit]

    def get_session_metadata(self, session_id: str) -> dict:
        """Get session metadata"""
        index_data = json.loads(self.index_file.read_text(encoding='utf-8'))
        for session in index_data.get("sessions", []):
            if session["session_id"] == session_id:
                return session
        raise ValueError(f"Session {session_id} not found")

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        session_dir = self.base_dir / session_id
        return session_dir.exists()

    def load_convergence_report(self, session_id: str) -> Optional[dict]:
        """Load convergence report for session"""
        session_dir = self.base_dir / session_id
        report_file = session_dir / "convergence_report.json"
        if report_file.exists():
            return json.loads(report_file.read_text(encoding='utf-8'))
        return None

    def load_reviews(self, session_id: str, version: int) -> List[dict]:
        """Load reviews for a PRD version"""
        session_dir = self.base_dir / session_id
        reviews_file = session_dir / f"reviews_v{version}.json"
        if reviews_file.exists():
            return json.loads(reviews_file.read_text(encoding='utf-8'))
        return []

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its data"""
        import shutil

        # Delete session directory
        session_dir = self.base_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)

        # Remove from index
        index_file = self.base_dir / "sessions_index.json"
        if index_file.exists():
            index_data = json.loads(index_file.read_text(encoding='utf-8'))
            index_data["sessions"] = [
                s for s in index_data.get("sessions", [])
                if s["session_id"] != session_id
            ]
            index_file.write_text(json.dumps(index_data, indent=2), encoding='utf-8')

        return True
