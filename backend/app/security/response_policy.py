"""Risk-based response recommendations for intercepted agent actions."""

from app.core.config import settings
from app.schemas.security import DecisionOutcome


class AdaptiveResponsePolicy:
    """Maps a validated risk score to a configurable response recommendation."""

    def __init__(
        self,
        require_approval_threshold: int = settings.REQUIRE_APPROVAL_RISK_THRESHOLD,
        escalate_threshold: int = settings.ESCALATE_RISK_THRESHOLD,
        block_threshold: int = settings.BLOCK_RISK_THRESHOLD,
    ):
        thresholds = (
            require_approval_threshold,
            escalate_threshold,
            block_threshold,
        )
        if any(not 0 <= threshold <= 100 for threshold in thresholds):
            raise ValueError("Response thresholds must be between 0 and 100")
        if not require_approval_threshold < escalate_threshold < block_threshold:
            raise ValueError(
                "Response thresholds must satisfy "
                "require_approval_threshold < escalate_threshold < block_threshold"
            )

        self.require_approval_threshold = require_approval_threshold
        self.escalate_threshold = escalate_threshold
        self.block_threshold = block_threshold

    def recommend(self, risk_score: int) -> tuple[DecisionOutcome, str]:
        """Return a response category and rationale for a 0-100 risk score."""
        if not 0 <= risk_score <= 100:
            raise ValueError("Risk score must be between 0 and 100")

        if risk_score >= self.block_threshold:
            return DecisionOutcome.BLOCK, (
                f"Risk score {risk_score} meets the block threshold "
                f"({self.block_threshold})."
            )
        if risk_score >= self.escalate_threshold:
            return DecisionOutcome.ESCALATE, (
                f"Risk score {risk_score} meets the escalation threshold "
                f"({self.escalate_threshold})."
            )
        if risk_score >= self.require_approval_threshold:
            return DecisionOutcome.REQUIRE_APPROVAL, (
                f"Risk score {risk_score} meets the approval threshold "
                f"({self.require_approval_threshold})."
            )
        return DecisionOutcome.ALLOW, (
            f"Risk score {risk_score} is below the approval threshold "
            f"({self.require_approval_threshold})."
        )