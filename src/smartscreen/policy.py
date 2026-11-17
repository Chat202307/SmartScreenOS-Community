from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allowed: bool
    reason: str
    payload: Dict[str, Any]

    def to_dict(self):
        return {
            "action": self.action,
            "allowed": self.allowed,
            "reason": self.reason,
            "payload": dict(self.payload),
        }

class PolicyEngine:
    def evaluate(self, proposal):
        proposal = dict(proposal or {})
        action = proposal.get("action", "none")

        if not proposal.get("human_value"):
            return PolicyDecision(
                action=action,
                allowed=False,
                reason="The proposal does not identify a real family need.",
                payload=proposal,
            )

        if proposal.get("priority") == "low" and proposal.get("requires_attention"):
            return PolicyDecision(
                action=action,
                allowed=False,
                reason="Low-priority information should not demand attention.",
                payload=proposal,
            )

        return PolicyDecision(
            action=action,
            allowed=True,
            reason="The proposal passed the current policy rules.",
            payload=proposal,
        )
