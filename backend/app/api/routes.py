"""
API routes for invoice reconciliation
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import os
import shutil
import uuid

from app.models.schemas import *
from app.services.agent_service import get_agent_service
from app.services.processing_service import get_processing_service
from app.services.report_service import get_report_service
from app.core.config import settings
from app.api.utils import format_result_for_frontend, process_invoice_background

import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    agent_service = get_agent_service()
    processing_service = get_processing_service()
    
    return HealthResponse(
        status="healthy",
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL,
        po_database_size=len(agent_service.po_database),
        active_jobs=processing_service.get_active_jobs_count()
    )


@router.post("/upload/invoice", response_model=FileUploadResponse)
async def upload_invoice(file: UploadFile = File(...)):
    """Upload invoice file (PDF or image)"""
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded invoice: {filename}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            path=file_path,
            size=os.path.getsize(file_path),
            uploaded_at=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/upload/po", response_model=FileUploadResponse)
async def upload_po(file: UploadFile = File(...)):
    """Upload and extract purchase order"""
    try:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded PO: {filename}")
        
        # Extract PO data
        agent_service = get_agent_service()
        from app.services import get_po_service
        from agents.po_extraction_agent import POExtractionAgent
        
        po_extractor = POExtractionAgent(llm=agent_service.llm)
        po_data = po_extractor.extract(file_path)
        
        # Add to database
        po_service = get_po_service()
        success = po_service.add_po(po_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add PO to database")
        
        # Reload matching agent's PO database
        agent_service = get_agent_service()
        agent_service.reload_po_database()
        
        logger.info(f"Extracted and added PO: {po_data.get('po_number')}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            path=file_path,
            size=os.path.getsize(file_path),
            uploaded_at=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"PO upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report/{job_id}/pdf")
async def download_report_pdf(job_id: str):
    """Generate and download PDF reconciliation report"""
    processing_service = get_processing_service()
    job = processing_service.get_job(job_id)
    
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Job result not found or not completed")
    
    result = job.get("result")
    report_service = get_report_service()
    
    # Create temporary PDF path
    from pathlib import Path
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    pdf_path = report_dir / f"report_{job_id}.pdf"
    
    try:
        report_service.generate_pdf_report(result, str(pdf_path))
        return FileResponse(
            path=pdf_path,
            filename=f"reconciliation_report_{job_id[:8]}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

@router.get("/pos")
async def get_pos():
    """Get list of all purchase orders"""
    try:
        from app.services.po_service import get_po_service
        
        po_service = get_po_service()
        po_summaries = po_service.get_po_summary_list()
        
        return {
            "total": len(po_summaries),
            "purchase_orders": po_summaries
        }
    
    except Exception as e:
        logger.error(f"Failed to get PO list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=JobResponse)
async def process_invoice(
    request: ProcessRequest,
    background_tasks: BackgroundTasks
):
    """Start processing an invoice"""
    try:
        # Find invoice file
        invoice_path = None
        for ext in settings.ALLOWED_EXTENSIONS:
            path = os.path.join(settings.UPLOAD_DIR, f"{request.invoice_file_id}{ext}")
            if os.path.exists(path):
                invoice_path = path
                break
        
        if not invoice_path:
            raise HTTPException(status_code=404, detail="Invoice file not found")
        
        # Find PO file (optional)
        po_path = None
        if request.po_file_id:
            # Check JSON first
            json_path = os.path.join(settings.UPLOAD_DIR, f"{request.po_file_id}.json")
            if os.path.exists(json_path):
                po_path = json_path
            else:
                # Check for other extensions
                for ext in ['.pdf', '.png', '.jpg']:
                    # Try both with and without "po_" prefix conventions if needed, 
                    # but current upload_po saves as "po_{uuid}.pdf" or just "{uuid}.ext" depending on implementation.
                    # Re-reading upload_po: it saves as `po_{uuid}.pdf` for non-json.
                    # BUT the file_id returned is just uuid.
                    
                    # Try pattern 1: po_{uuid}{ext}
                    path1 = os.path.join(settings.UPLOAD_DIR, f"po_{request.po_file_id}{ext}")
                    if os.path.exists(path1):
                        po_path = path1
                        break
                    
                    # Try pattern 2: {uuid}{ext} (fallback)
                    path2 = os.path.join(settings.UPLOAD_DIR, f"{request.po_file_id}{ext}")
                    if os.path.exists(path2):
                        po_path = path2
                        break

            if not po_path:
                logger.warning(f"PO file ID {request.po_file_id} provided but file not found")
        
        # Create job
        processing_service = get_processing_service()
        job_id = processing_service.create_job(invoice_path, po_path)
        
        # Start background processing
        background_tasks.add_task(
            process_invoice_background,
            job_id,
            invoice_path,
            po_path
        )
        
        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Invoice processing started"
        )
    
    except Exception as e:
        logger.error(f"Process start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Get processing status"""
    processing_service = get_processing_service()
    job = processing_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return StatusResponse(
        job_id=job_id,
        status=JobStatus(job['status']),
        current_agent=job.get('current_agent'),
        progress=job['progress'],
        message=job['message'],
        created_at=job.get('created_at'),
        completed_at=job.get('completed_at')
    )


@router.get("/result/{job_id}", response_model=ProcessingResult)
async def get_result(job_id: str):
    """Get processing result"""
    processing_service = get_processing_service()
    job = processing_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )
    
    return job.get('result')


@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download result as JSON"""
    result_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_result.json")
    
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        result_path,
        media_type="application/json",
        filename=f"invoice_result_{job_id}.json"
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs():
    """List recent processing jobs"""
    processing_service = get_processing_service()
    jobs = processing_service.get_all_jobs()
    
    # Convert to list and sort by created_at descending
    all_jobs = []
    for job_id, job in jobs.items():
        # Get recommendation action from result if job is completed
        recommendation_action = None
        if job.get('status') == 'completed' and job.get('result'):
            resolution = job['result'].get('resolution', {})
            recommendation_action = resolution.get('action')

        all_jobs.append(JobListItem(
            job_id=job_id,
            status=JobStatus(job['status']),
            progress=job['progress'],
            created_at=job.get('created_at'),
            message=job['message'],
            recommendation_action=recommendation_action
        ))
    
    # Sort by created_at (newest first)
    all_jobs.sort(key=lambda x: x.created_at or "", reverse=True)
    
    # Limit to 5
    recent_jobs = all_jobs[:5]
    
    return JobListResponse(
        total=len(jobs),
        jobs=recent_jobs
    )


@router.patch("/job/{job_id}/action")
async def update_job_action(job_id: str, request: UpdateJobActionRequest):
    """Update manual action for a job"""
    processing_service = get_processing_service()
    job = processing_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job['status'] != 'completed' or not job.get('result'):
        raise HTTPException(status_code=400, detail="Can only update action for completed jobs")
    
    # Update action in result
    job['result']['resolution']['action'] = request.action
    
    # Also update the result file on disk if it exists
    result_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_result.json")
    if os.path.exists(result_path):
        import json
        with open(result_path, 'w') as f:
            json.dump(job['result'], f, indent=2, default=str)
            
    return {"message": "Action updated successfully", "action": request.action}


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """Delete a job"""
    processing_service = get_processing_service()
    job = processing_service.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete result file
    result_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_result.json")
    if os.path.exists(result_path):
        os.remove(result_path)
    
    processing_service.delete_job(job_id)
    
    return {"message": "Job deleted successfully"}


@router.get("/po/list", response_model=POListResponse)
async def list_pos():
    """List all purchase orders"""
    agent_service = get_agent_service()
    
    return POListResponse(
        total=len(agent_service.po_database),
        purchase_orders=[
            PurchaseOrderSummary(
                po_number=po.get('po_number'),
                supplier=po.get('supplier'),
                total=po.get('total'),
                currency=po.get('currency'),
                line_items_count=len(po.get('line_items', []))
            )
            for po in agent_service.po_database
        ]
    )


@router.get("/po/{po_number}")
async def get_po(po_number: str):
    """Get specific purchase order"""
    agent_service = get_agent_service()
    po = agent_service.get_po_by_number(po_number)
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    return po


@router.get("/stats", response_model=StatisticsResponse)
async def get_stats():
    """Get system statistics"""
    agent_service = get_agent_service()
    processing_service = get_processing_service()
    stats = processing_service.get_statistics()
    
    return StatisticsResponse(
        total_invoices_processed=stats['total_processed'],
        auto_approved=stats['auto_approved'],
        requires_review=stats['requires_review'],
        active_processing=stats['active'],
        failed=stats['failed'],
        po_database_size=len(agent_service.po_database)
    )