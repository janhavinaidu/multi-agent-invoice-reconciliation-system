"""
Shared state definitions for the invoice reconciliation system.
This state is passed between agents in the LangGraph workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for discrepancies"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class RecommendedAction(str, Enum):
    """Possible recommendation actions"""
    AUTO_APPROVE = "auto_approve"
    UNAPPROVED = "unapproved"
    PENDING = "pending"
    REQUEST_CLARIFICATION = "request_clarification"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class LineItem(TypedDict, total=False):
    """Structure for a single line item"""
    item_number: str
    description: str
    quantity: float
    unit_price: float
    total_price: float
    unit: str
    confidence: float


class ExtractionResult(TypedDict, total=False):
    """Results from document intelligence agent"""
    invoice_number: str
    supplier_name: str
    supplier_address: str
    invoice_date: str
    due_date: Optional[str]
    po_reference: Optional[str]
    line_items: List[LineItem]
    subtotal: Optional[float]
    tax: Optional[float]
    total: float
    currency: str
    confidence_score: float
    extraction_metadata: Dict[str, Any]
    ocr_quality: str
    warnings: List[str]


class MatchResult(TypedDict, total=False):
    """Results from matching agent"""
    po_number: Optional[str]
    match_type: str  # exact, fuzzy, semantic, none
    match_confidence: float
    matched_items: List[Dict[str, Any]]
    unmatched_items: List[Dict[str, Any]]
    fuzzy_matches: List[Dict[str, Any]]
    reasoning: str


class Discrepancy(TypedDict, total=False):
    """Structure for a detected discrepancy"""
    discrepancy_id: str
    type: str
    severity: SeverityLevel
    confidence: float
    line_item_index: Optional[int]
    expected_value: Any
    actual_value: Any
    difference: Any
    percentage_difference: Optional[float]
    details: str
    reasoning: str


class Recommendation(TypedDict, total=False):
    """Structure for resolution recommendation"""
    action: RecommendedAction
    confidence: float
    reasoning: str
    summary: str
    risk_assessment: str
    suggested_next_steps: List[str]
    requires_human_review: bool
    estimated_financial_impact: Optional[float]


class AgentStep(TypedDict, total=False):
    """Record of an agent's decision-making process"""
    agent_name: str
    timestamp: str
    input_summary: str
    reasoning: str
    confidence: float
    output_summary: str
    execution_time: float


class InvoiceState(TypedDict, total=False):
    """
    Shared LangGraph state for invoice processing
    """

    # Input
    invoice_path: str
    invoice_filename: str
    uploaded_po_path: Optional[str]
    po_database: List[Dict[str, Any]]

    # Processing metadata
    processing_id: str
    processing_started: str
    processing_completed: Optional[str]
    current_agent: str

    # Agent outputs
    extraction_result: Optional[ExtractionResult]
    match_result: Optional[MatchResult]
    matched_po: Optional[Dict[str, Any]]
    discrepancies: List[Discrepancy]
    recommendation: Optional[Recommendation]

    # Reasoning chain
    agent_steps: List[AgentStep]

    # Error handling
    errors: List[Dict[str, Any]]
    requires_retry: bool
    retry_count: int

    # Configuration
    app_config: Dict[str, Any]

    # Final status
    status: str  # processing, completed, failed, requires_review
    overall_confidence: float


def create_initial_state(
    invoice_path: str,
    config: Dict[str, Any],
    po_database: List[Dict[str, Any]],
    uploaded_po_path: Optional[str] = None
) -> InvoiceState:
    """Create initial state for a new invoice"""
    import os
    import uuid

    return InvoiceState(
        invoice_path=invoice_path,
        invoice_filename=os.path.basename(invoice_path),
        uploaded_po_path=uploaded_po_path,
        po_database=po_database,
        processing_id=str(uuid.uuid4()),
        processing_started=datetime.utcnow().isoformat(),
        processing_completed=None,
        current_agent="document_intelligence",
        extraction_result=None,
        match_result=None,
        matched_po=None,
        discrepancies=[],
        recommendation=None,
        agent_steps=[],
        errors=[],
        requires_retry=False,
        retry_count=0,
        app_config=config,
        status="processing",
        overall_confidence=0.0
    )


def add_agent_step(
    state: InvoiceState,
    agent_name: str,
    reasoning: str,
    confidence: float,
    input_summary: str,
    output_summary: str,
    execution_time: float
) -> InvoiceState:
    """Add a step to the agent reasoning chain"""

    step = AgentStep(
        agent_name=agent_name,
        timestamp=datetime.utcnow().isoformat(),
        input_summary=input_summary,
        reasoning=reasoning,
        confidence=confidence,
        output_summary=output_summary,
        execution_time=execution_time
    )

    state["agent_steps"].append(step)
    return state


def add_error(
    state: InvoiceState,
    agent_name: str,
    error_message: str,
    error_type: str
) -> InvoiceState:
    """Add an error to the state"""

    error = {
        "agent": agent_name,
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": error_type,
        "message": error_message
    }

    state["errors"].append(error)
    return state


def calculate_overall_confidence(state: InvoiceState) -> float:
    """Calculate overall confidence based on all agent outputs"""

    confidences = []

    if state.get("extraction_result"):
        confidences.append(state["extraction_result"].get("confidence_score", 0.0))

    if state.get("match_result"):
        confidences.append(state["match_result"].get("match_confidence", 0.0))

    if state.get("recommendation"):
        confidences.append(state["recommendation"].get("confidence", 0.0))

    if confidences:
        return sum(confidences) / len(confidences)

    return 0.0
