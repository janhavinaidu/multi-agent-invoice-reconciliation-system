import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Package, Calendar, Building2 } from "lucide-react";

interface POSummary {
    po_number: string;
    vendor: string;
    order_date?: string;
    status?: string;
    item_count: number;
}

interface POHistoryProps {
    pos: POSummary[];
}

export default function POHistory({ pos }: POHistoryProps) {
    if (!pos || pos.length === 0) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Package className="h-5 w-5" />
                        Purchase Order Database
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-muted-foreground">
                        No purchase orders in database. Upload a PO to get started.
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Package className="h-5 w-5" />
                    Purchase Order Database ({pos.length})
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {pos.map((po, index) => (
                        <div
                            key={index}
                            className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
                        >
                            <div className="flex-1">
                                <div className="font-medium text-sm">{po.po_number}</div>
                                <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                                    <span className="flex items-center gap-1">
                                        <Building2 className="h-3 w-3" />
                                        {po.vendor}
                                    </span>
                                    {po.order_date && (
                                        <span className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            {po.order_date}
                                        </span>
                                    )}
                                    <span>{po.item_count} items</span>
                                </div>
                            </div>
                            {po.status && (
                                <span className={`px-2 py-1 text-xs rounded-full ${po.status === 'unapproved'
                                        ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                                        : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                                    }`}>
                                    {po.status}
                                </span>
                            )}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
