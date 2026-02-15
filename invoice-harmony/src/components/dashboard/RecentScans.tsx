import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { History, Calendar, FileText, CheckCircle2, XCircle, Clock, AlertCircle, Check, X, Download } from "lucide-react";
import { JobListItem, api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

interface RecentScansProps {
    scans: JobListItem[];
    onRefresh: () => void;
}

export default function RecentScans({ scans, onRefresh }: RecentScansProps) {
    const { toast } = useToast();

    const getStatusIcon = (status: string, action?: string) => {
        if (status === 'processing') return <Clock className="h-4 w-4 animate-spin text-blue-500" />;
        if (status === 'failed') return <XCircle className="h-4 w-4 text-destructive" />;

        switch (action) {
            case 'auto_approve':
                return <CheckCircle2 className="h-4 w-4 text-success" />;
            case 'unapproved':
                return <XCircle className="h-4 w-4 text-destructive" />;
            case 'pending':
            case 'escalate_to_human':
            case 'request_clarification':
                return <AlertCircle className="h-4 w-4 text-warning" />;
            default:
                return <FileText className="h-4 w-4 text-muted-foreground" />;
        }
    };

    const getStatusBadge = (status: string, action?: string) => {
        if (status === 'processing') return <Badge variant="secondary" className="bg-blue-100 text-blue-700">Processing</Badge>;
        if (status === 'failed') return <Badge variant="destructive">Failed</Badge>;
        if (status === 'pending') return <Badge variant="secondary">Queued</Badge>;

        if (!action) return <Badge variant="outline">Completed</Badge>;

        switch (action) {
            case 'auto_approve':
                return <Badge className="bg-success/20 text-success hover:bg-success/30 border-success/30">Approved</Badge>;
            case 'unapproved':
                return <Badge variant="destructive" className="bg-red-100 text-red-700 hover:bg-red-200 border-red-200">Unapproved</Badge>;
            case 'pending':
                return <Badge className="bg-warning/20 text-warning hover:bg-warning/30 border-warning/30">Pending</Badge>;
            case 'escalate_to_human':
                return <Badge className="bg-warning/20 text-warning hover:bg-warning/30 border-warning/30">Escalated</Badge>;
            default:
                return <Badge variant="outline">{action}</Badge>;
        }
    };

    const handleAction = async (e: React.MouseEvent, jobId: string, action: string) => {
        e.stopPropagation();
        try {
            await api.updateJobAction(jobId, action);
            toast({
                title: "Status Updated",
                description: `Scan status changed to ${action.replace('_', ' ')}`,
            });
            onRefresh();
        } catch (error) {
            toast({
                title: "Error",
                description: "Failed to update status",
                variant: "destructive"
            });
        }
    };

    const handleDownload = async (e: React.MouseEvent, jobId: string, invoiceNumber?: string) => {
        e.stopPropagation();
        try {
            toast({ title: "Downloading Report...", description: "Preparing PDF" });
            const blob = await api.downloadReportPdf(jobId);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `reconciliation-report-${invoiceNumber || jobId.slice(0, 8)}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            toast({
                title: "Download Failed",
                description: "Could not generate report",
                variant: "destructive"
            });
        }
    };

    if (!scans || scans.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <History className="h-5 w-5" />
                        Recent Scans
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">
                        No recent scans found. Upload an invoice to get started.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="shadow-card">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <History className="h-5 w-5" />
                    Recent Scans
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {scans.map((scan) => (
                        <div
                            key={scan.job_id}
                            onClick={(e) => handleDownload(e, scan.job_id)}
                            className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent/50 transition-all cursor-pointer group"
                        >
                            <div className="flex items-center gap-4">
                                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted group-hover:bg-primary/10 transition-colors">
                                    {getStatusIcon(scan.status, scan.recommendation_action)}
                                </div>
                                <div>
                                    <div className="font-medium text-sm flex items-center gap-2">
                                        Scan #{scan.job_id.slice(0, 8)}
                                    </div>
                                    <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                                        <span className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            {scan.created_at ? new Date(scan.created_at).toLocaleString() : "Recently"}
                                        </span>
                                        <span className="max-w-[200px] truncate">{scan.message}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                {/* Actions */}
                                {scan.status === 'completed' && (
                                    <div className="flex items-center gap-1 bg-muted/30 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7 rounded-full hover:bg-success/20 hover:text-success"
                                            onClick={(e) => handleAction(e, scan.job_id, 'auto_approve')}
                                            title="Approve"
                                        >
                                            <Check className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7 rounded-full hover:bg-destructive/20 hover:text-destructive"
                                            onClick={(e) => handleAction(e, scan.job_id, 'unapproved')}
                                            title="Unapprove"
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7 rounded-full hover:bg-primary/20 hover:text-primary"
                                            onClick={(e) => handleDownload(e, scan.job_id)}
                                            title="Download Report"
                                        >
                                            <Download className="h-4 w-4" />
                                        </Button>
                                    </div>
                                )}

                                <div className="min-w-[100px] flex justify-end">
                                    {getStatusBadge(scan.status, scan.recommendation_action)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
