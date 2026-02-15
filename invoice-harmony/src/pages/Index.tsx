import { useState, useEffect, useRef } from "react";
import Header from "@/components/dashboard/Header";
import UploadCard from "@/components/dashboard/UploadCard";
import StatusStepper, { AgentStep } from "@/components/dashboard/StatusStepper";
import InvoiceDataCard from "@/components/dashboard/InvoiceDataCard";
import MatchingResultsCard from "@/components/dashboard/MatchingResultsCard";
import DiscrepancyTable from "@/components/dashboard/DiscrepancyTable";
import RecommendationCard from "@/components/dashboard/RecommendationCard";
import AgentTimeline from "@/components/dashboard/AgentTimeline";
import RecentScans from "@/components/dashboard/RecentScans";
import { useToast } from "@/hooks/use-toast";
import { api, transformBackendData, JobListItem } from "@/lib/api";
import { initialProcessingSteps } from "@/data/mockData";
import { Button } from "@/components/ui/button";
import { RefreshCcw, ArrowLeft } from "lucide-react";

const Index = () => {
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [currentSteps, setCurrentSteps] = useState<AgentStep[]>(initialProcessingSteps);

  // Result State
  const [resultData, setResultData] = useState<any>(null);

  // Scan History State
  const [scanList, setScanList] = useState<JobListItem[]>([]);

  // Polling ref to stop polling if component unmounts
  const pollingRef = useRef<boolean>(false);

  // Fetch scan list on mount
  useEffect(() => {
    fetchScanList();
  }, []);

  const fetchScanList = async () => {
    try {
      const response = await api.getJobs();
      setScanList(response.jobs || []);
    } catch (error) {
      console.error("Failed to fetch scan list:", error);
    }
  };

  const handleReset = () => {
    setProcessingComplete(false);
    setIsProcessing(false);
    setResultData(null);
    setCurrentSteps(initialProcessingSteps);
    pollingRef.current = false;
    fetchScanList();
  };

  const handleProcessing = async (invoiceFile: File, poFile: File | null) => {
    setIsProcessing(true);
    setProcessingComplete(false);
    setResultData(null);
    setCurrentSteps(initialProcessingSteps);
    pollingRef.current = true;

    try {
      // 1. Upload Invoice
      toast({ title: "Uploading Invoice...", description: invoiceFile.name });
      const invoiceRes = await api.uploadInvoice(invoiceFile);

      // 2. Upload PO (optional)
      let poFileId = undefined;
      if (poFile) {
        toast({ title: "Uploading Purchase Order...", description: poFile.name });
        const poRes = await api.uploadPO(poFile);
        if (poRes.file_id) poFileId = poRes.file_id;
        toast({ title: "PO Added", description: "Purchase order added to database" });
      }

      // 3. Start Processing
      toast({ title: "Starting Processing...", description: "Initializing agents" });
      const jobRes = await api.processInvoice(invoiceRes.file_id, poFileId);
      const jobId = jobRes.job_id;

      // 4. Poll Status
      pollStatus(jobId);

    } catch (error: any) {
      console.error(error);
      setIsProcessing(false);
      pollingRef.current = false;
      toast({
        title: "Error",
        description: error.message || "An error occurred during processing",
        variant: "destructive",
      });
    }
  };

  const pollStatus = async (jobId: string) => {
    if (!pollingRef.current) return;

    try {
      const statusRes = await api.checkStatus(jobId);

      // Update Steps based on statusRes.current_agent
      updateSteps(statusRes.current_agent, statusRes.status);

      if (statusRes.status === "completed") {
        pollingRef.current = false;
        finishProcessing(jobId);
      } else if (statusRes.status === "failed") {
        pollingRef.current = false;
        setIsProcessing(false);
        toast({ title: "Processing Failed", description: statusRes.message, variant: "destructive" });
        fetchScanList();
      } else {
        // Continue polling
        setTimeout(() => pollStatus(jobId), 2000);
      }
    } catch (error) {
      console.error("Polling error", error);
      // Determine if we should stop or retry
      setTimeout(() => pollStatus(jobId), 2000);
    }
  };

  const updateSteps = (currentAgent: string | undefined, status: string) => {
    setCurrentSteps((prev) => {
      const newSteps = [...prev];

      // Map backend agent names to frontend IDs
      const agentMap: Record<string, string> = {
        'document_intelligence': 'document',
        'matching': 'matching',
        'discrepancy_detection': 'discrepancy',
        'resolution': 'resolution'
      };

      if (!currentAgent) return newSteps;

      const activeId = agentMap[currentAgent];
      if (!activeId) return newSteps;

      const activeIndex = newSteps.findIndex(s => s.id === activeId);

      if (activeIndex !== -1) {
        // Mark previous as complete
        for (let i = 0; i < activeIndex; i++) {
          newSteps[i] = { ...newSteps[i], status: 'complete' };
        }
        // Mark current as running
        newSteps[activeIndex] = { ...newSteps[activeIndex], status: 'running' };
      }

      return newSteps;
    });
  };

  const finishProcessing = async (jobId: string) => {
    try {
      const result = await api.getResult(jobId);
      console.log("[DEBUG] Raw backend result:", result);

      const formatted = transformBackendData(result);
      console.log("[DEBUG] Transformed data:", formatted);

      setResultData({ ...formatted, jobId });

      // Mark all steps complete
      setCurrentSteps(prev => prev.map(s => ({ ...s, status: 'complete' })));

      setIsProcessing(false);
      setProcessingComplete(true);
      fetchScanList();
      toast({
        title: "Processing Complete",
        description: "Invoice reconciliation has been completed successfully.",
      });
    } catch (error) {
      console.error("Result fetch error", error);
      setIsProcessing(false);
    }
  };

  const handleApprove = () => {
    toast({
      title: "Invoice Approved",
      description: "The invoice has been approved and moved to payment processing.",
    });
  };

  const handleUnapprove = () => {
    toast({
      title: "Invoice Unapproved",
      description: "The invoice has been rejected. Feedback sent to supplier.",
      variant: "destructive",
    });
  };

  const handleEscalate = () => {
    toast({
      title: "Job Pending Review",
      description: "The invoice has been placed in the pending queue for human review.",
    });
  };

  const handleDownload = async () => {
    if (!resultData || !resultData.jobId) return;

    try {
      toast({ title: "Generating Report...", description: "Preparing your PDF report" });
      const blob = await api.downloadReportPdf(resultData.jobId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reconciliation-report-${resultData.invoiceData.invoiceNumber}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Report Downloaded",
        description: "Your PDF reconciliation report is ready.",
      });
    } catch (error) {
      console.error("Download error", error);
      toast({
        title: "Download Failed",
        description: "Could not generate PDF report. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="container mx-auto px-6 py-8">
        {/* Results Toolbar */}
        {(processingComplete || isProcessing) && (
          <div className="mb-6 flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              className="group flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
              Back to Upload
            </Button>
            {processingComplete && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleReset}
                className="flex items-center gap-2"
              >
                <RefreshCcw className="h-4 w-4" />
                New Scan
              </Button>
            )}
          </div>
        )}

        {/* Upload and Status Section */}
        {!processingComplete && (
          <div className="mb-8 grid gap-6 lg:grid-cols-2">
            <UploadCard onProcess={handleProcessing} isProcessing={isProcessing} />
            <StatusStepper steps={currentSteps} />
          </div>
        )}

        {/* Results Section - Only shown after processing */}
        {processingComplete && resultData && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Extracted Data and Matching */}
            <div className="grid gap-6 xl:grid-cols-2">
              <InvoiceDataCard data={resultData.invoiceData} />
              <MatchingResultsCard data={resultData.matchingResult} />
            </div>

            {/* Discrepancies and Recommendation */}
            <div className="grid gap-6 xl:grid-cols-2">
              <DiscrepancyTable discrepancies={resultData.discrepancies} />
              <RecommendationCard
                recommendation={resultData.recommendation}
                onApprove={handleApprove}
                onUnapprove={handleUnapprove}
                onEscalate={handleEscalate}
                onDownload={handleDownload}
              />
            </div>

            {/* Agent Timeline */}
            <AgentTimeline agents={resultData.agentReasoning} />
          </div>
        )}

        {/* Empty State when not processed */}
        {!processingComplete && !isProcessing && (
          <div className="space-y-6">
            {/* Recent Scans (was POHistory) */}
            <RecentScans scans={scanList} onRefresh={fetchScanList} />

            {/* Empty State Message */}
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-muted/30 py-16">
              <div className="text-center">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <svg
                    className="h-8 w-8 text-muted-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-foreground">
                  Ready for Reconciliation
                </h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  Upload an invoice and purchase order to begin the AI reconciliation process
                </p>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
};

export default Index;
