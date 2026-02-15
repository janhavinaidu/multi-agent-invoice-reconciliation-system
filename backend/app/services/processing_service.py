"""
Service for managing invoice processing jobs
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProcessingService:
    """Manage processing jobs and their state"""
    
    def __init__(self):
        """Initialize processing service"""
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, invoice_path: str, po_path: Optional[str] = None) -> str:
        """Create a new processing job"""
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "current_agent": "document_intelligence",
            "progress": 0,
            "message": "Job queued for processing",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "invoice_path": invoice_path,
            "po_path": po_path,
            "result": None,
            "error": None
        }
        
        logger.info(f"Created job {job_id} for invoice {invoice_path}")
        return job_id
    
    def update_job(self, job_id: str, **kwargs):
        """Update job status"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        self.jobs[job_id].update(kwargs)
        logger.debug(f"Updated job {job_id}: {kwargs}")
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs"""
        return self.jobs
    
    def delete_job(self, job_id: str):
        """Delete a job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Deleted job {job_id}")
    
    def get_active_jobs_count(self) -> int:
        """Count active processing jobs"""
        return sum(1 for job in self.jobs.values() if job['status'] == 'processing')
    
    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics"""
        completed = [j for j in self.jobs.values() if j['status'] == 'completed']
        
        auto_approved = sum(
            1 for j in completed
            if j.get('result', {}).get('resolution', {}).get('action') == 'auto_approve'
        )
        
        return {
            "total_processed": len(completed),
            "auto_approved": auto_approved,
            "requires_review": len(completed) - auto_approved,
            "active": sum(1 for j in self.jobs.values() if j['status'] == 'processing'),
            "failed": sum(1 for j in self.jobs.values() if j['status'] == 'failed'),
            "pending": sum(1 for j in self.jobs.values() if j['status'] == 'pending')
        }


# Global service instance
_processing_service = None


def get_processing_service() -> ProcessingService:
    """Get or create processing service instance"""
    global _processing_service
    if _processing_service is None:
        _processing_service = ProcessingService()
    return _processing_service