from typing import Dict
from api.models.api_models import RefinementStatus

# Shared state to avoid circular imports
active_refinements: Dict[str, RefinementStatus] = {}