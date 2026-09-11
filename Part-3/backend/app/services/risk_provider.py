from abc import ABC, abstractmethod
from app.schemas.action import ProposedAction
from app.schemas.decision import RiskResult


class RiskProvider(ABC):
    """
    Abstract Risk Provider Interface.
    Part 3 interacts solely with this interface to retrieve risk scores and risk factors.
    Allows seamless drop-in of the real Part 2 Detection & Risk Engine API without
    modifying the Policy Engine or Decision Engine.
    """

    @abstractmethod
    def get_risk(self, action: ProposedAction) -> RiskResult:
        """
        Calculates or retrieves risk analysis for the proposed action.
        Returns RiskResult containing risk_score (0-100) and risk_factors (0-100 each).
        """
        pass
