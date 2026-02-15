"""
Pydantic models for request/response schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentName(str, Enum):
    """Agent names"""
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    MATCHING = "matching"
    DISCREPANCY_DETECTION = "discrepancy_detection"
    RESOLUTION = "resolution"


class SeverityLevel(str, Enum):
    """Discrepancy severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class RecommendedAction(str, Enum):
    """Resolution actions"""
    AUTO_APPROVE = "auto_approve"
    REQUEST_CLARIFICATION = "request_clarification"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    REJECT = "reject"
    UNAPPROVED = "unapproved"
    PENDING = "pending"


# Request Models

class ProcessRequest(BaseModel):
    """Request to process an invoice"""
    invoice_file_id: str = Field(..., description="ID of uploaded invoice file")
    po_file_id: Optional[str] = Field(None, description="Optional PO file ID")


class UpdateJobActionRequest(BaseModel):
    """Request to update job manual action"""
    action: RecommendedAction


# Response Models

class FileUploadResponse(BaseModel):
    """Response from file upload"""
    file_id: str
    filename: str
    path: str
    size: int
    uploaded_at: str


class JobResponse(BaseModel):
    """Response when starting a job"""
    job_id: str
    status: JobStatus
    message: str


class StatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: JobStatus
    current_agent: Optional[str] = None
    progress: int = Field(..., ge=0, le=100)
    message: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class LineItem(BaseModel):
    """Invoice line item"""
    item_number: Optional[str] = None
    description: str
    quantity: float
    unit: Optional[str] = None
    unit_price: float
    total_price: float
    confidence: Optional[float] = None


class ExtractionData(BaseModel):
    """Extracted invoice data"""
    invoice_number: Optional[str]
    supplier: Optional[str]
    po_reference: Optional[str]
    total_amount: float
    line_items: List[LineItem]
    confidence: float = Field(..., ge=0, le=1)


class MatchedItem(BaseModel):
    """Matched line item"""
    invoice_item: Dict[str, Any]
    po_item: Optional[Dict[str, Any]]
    match_score: float
    match_type: str


class MatchingData(BaseModel):
    """Matching results"""
    match_type: str
    confidence_score: float = Field(..., ge=0, le=1)
    matched_po_id: Optional[str]
    matched_items: List[MatchedItem] = []
    matched_items_count: int
    unmatched_items: List[Dict[str, Any]] = []
    unmatched_items_count: int


class DiscrepancyData(BaseModel):
    """Discrepancy information"""
    type: str
    severity: SeverityLevel
    confidence: float = Field(..., ge=0, le=1)
    explanation: str
    details: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    difference: Optional[float] = None


class ResolutionData(BaseModel):
    """Resolution recommendation"""
    action: RecommendedAction
    risk_level: str
    financial_impact: float
    ai_reasoning: str
    suggested_steps: List[str]


class AgentStep(BaseModel):
    """Agent reasoning step"""
    agent: str
    timestamp: str
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    execution_time: float


class ProcessingResult(BaseModel):
    """Complete processing result"""
    extraction: ExtractionData
    matching: MatchingData
    discrepancies: List[DiscrepancyData]
    resolution: ResolutionData
    agent_timeline: List[AgentStep]


class JobListItem(BaseModel):
    """Job list item"""
    job_id: str
    status: JobStatus
    progress: int
    created_at: Optional[str]
    message: str
    recommendation_action: Optional[RecommendedAction] = None


class JobListResponse(BaseModel):
    """List of jobs"""
    total: int
    jobs: List[JobListItem]


class PurchaseOrderSummary(BaseModel):
    """PO summary"""
    po_number: str
    supplier: str
    total: float
    currency: str
    line_items_count: int


class POListResponse(BaseModel):
    """List of purchase orders"""
    total: int
    purchase_orders: List[PurchaseOrderSummary]


class StatisticsResponse(BaseModel):
    """System statistics"""
    total_invoices_processed: int
    auto_approved: int
    requires_review: int
    active_processing: int
    failed: int
    po_database_size: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    llm_provider: str
    llm_model: str
    po_database_size: int
    active_jobs: int