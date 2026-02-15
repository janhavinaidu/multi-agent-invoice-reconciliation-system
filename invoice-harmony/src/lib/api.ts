import { AgentStep } from "@/components/dashboard/StatusStepper";

const API_Base = "http://localhost:8000/api";

export interface FileUploadResponse {
    file_id: string;
    filename: string;
    path: string;
}

export interface JobResponse {
    job_id: string;
    status: string;
    message: string;
}

export interface StatusResponse {
    job_id: string;
    status: string;
    current_agent?: string;
    progress: number;
    message: string;
}

export interface JobListItem {
    job_id: string;
    status: string;
    progress: number;
    created_at?: string;
    message: string;
    recommendation_action?: string;
}

export interface JobListResponse {
    total: number;
    jobs: JobListItem[];
}

export interface ProcessingResult {
    extraction: any;
    matching: any;
    discrepancies: any[];
    resolution: any;
    agent_timeline: any[];
}

export const api = {
    getJobs: async (): Promise<JobListResponse> => {
        const res = await fetch(`${API_Base}/jobs`);
        if (!res.ok) throw new Error("Failed to fetch jobs");
        return res.json();
    },
    uploadInvoice: async (file: File): Promise<FileUploadResponse> => {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_Base}/upload/invoice`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("Invoice upload failed");
        return res.json();
    },

    uploadPO: async (file: File): Promise<any> => {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_Base}/upload/po`, {
            method: "POST",
            body: formData,
        });
        if (!res.ok) throw new Error("PO upload failed");
        return res.json();
    },

    getPOs: async (): Promise<any> => {
        const res = await fetch(`${API_Base}/pos`);
        if (!res.ok) throw new Error("Failed to fetch POs");
        return res.json();
    },

    processInvoice: async (invoiceFileId: string, poFileId?: string): Promise<JobResponse> => {
        const res = await fetch(`${API_Base}/process`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                invoice_file_id: invoiceFileId,
                po_file_id: poFileId,
            }),
        });
        if (!res.ok) throw new Error("Processing start failed");
        return res.json();
    },

    checkStatus: async (jobId: string): Promise<StatusResponse> => {
        const res = await fetch(`${API_Base}/status/${jobId}`);
        if (!res.ok) throw new Error("Status check failed");
        return res.json();
    },

    getResult: async (jobId: string): Promise<ProcessingResult> => {
        const res = await fetch(`${API_Base}/result/${jobId}`);
        if (!res.ok) throw new Error("Result fetch failed");
        return res.json();
    },

    downloadReportPdf: async (jobId: string): Promise<Blob> => {
        const res = await fetch(`${API_Base}/report/${jobId}/pdf`);
        if (!res.ok) throw new Error("Report download failed");
        return res.blob();
    },
    updateJobAction: async (jobId: string, action: string): Promise<any> => {
        const res = await fetch(`${API_Base}/job/${jobId}/action`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ action }),
        });
        if (!res.ok) throw new Error("Failed to update job action");
        return res.json();
    },
};

// Transformer to convert snake_case backend data to camelCase frontend data
export const transformBackendData = (data: ProcessingResult) => {
    return {
        invoiceData: {
            invoiceNumber: data.extraction.invoice_number,
            supplier: data.extraction.supplier,
            poReference: data.extraction.po_reference,
            totalAmount: data.extraction.total_amount,
            lineItems: data.extraction.line_items.map((item: any) => ({
                description: item.description,
                quantity: item.quantity,
                unitPrice: item.unit_price,
                total: item.total_price
            }))
        },
        matchingResult: {
            matchType: data.matching.match_type,
            confidence: Math.round(data.matching.confidence_score * 100),
            matchedPoId: data.matching.matched_po_id,
            matchedItems: data.matching.matched_items.map((m: any) => m.invoice_item.description), // Simplified for display
            unmatchedItems: data.matching.unmatched_items.map((u: any) => u.invoice_item?.description || "Unknown Item")
        },
        discrepancies: data.discrepancies.map((d: any) => ({
            type: d.type,
            severity: d.severity,
            confidence: Math.round(d.confidence * 100),
            explanation: d.explanation,
            field: d.type,
            expectedValue: String(d.expected_value || ""),
            actualValue: String(d.actual_value || "")
        })),
        recommendation: {
            decision: data.resolution.action,
            riskLevel: data.resolution.risk_level,
            financialImpact: data.resolution.financial_impact,
            reasoning: data.resolution.ai_reasoning,
            summary: data.resolution.summary,
            suggestedSteps: data.resolution.suggested_steps
        },
        agentReasoning: data.agent_timeline.map((step: any) => ({
            id: step.agent,
            agentName: formatAgentName(step.agent),
            reasoning: step.reasoning,
            confidence: Math.round(step.confidence * 100),
            executionTime: Math.round((step.execution_time || 0) * 1000), // s to ms
            timestamp: step.timestamp ? new Date(step.timestamp).toLocaleTimeString() : "N/A"
        }))
    };
};

const formatAgentName = (id: string) => {
    return id.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};
