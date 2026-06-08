from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    source_system: str
    source_object_id: str
    changed_fields: List[str]
    risk_hint: str
    related_goal_id: str
    occurred_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ExecutionIntent:
    intent_id: str
    goal_id: str
    initiator: str
    requested_action: str
    source_refs: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class ExecutionPreview:
    intent_id: str
    impacted_modules: List[str]
    actions: List[str]
    requires_confirmation: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class ExecutionResult:
    intent_id: str
    status: str
    writebacks: List[str] = field(default_factory=list)
    verification_notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class KnowledgeUpdate:
    asset_type: str
    title: str
    summary: str
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
