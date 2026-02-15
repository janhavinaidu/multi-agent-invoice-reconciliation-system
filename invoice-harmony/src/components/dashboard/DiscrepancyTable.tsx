import { AlertTriangle, AlertCircle, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export interface Discrepancy {
  type: "price" | "quantity" | "missing_po" | "duplicate" | "date_mismatch";
  severity: "critical" | "warning" | "clean";
  confidence: number;
  explanation: string;
  field?: string;
  expectedValue?: string;
  actualValue?: string;
}

interface DiscrepancyTableProps {
  discrepancies: Discrepancy[];
}

const DiscrepancyTable = ({ discrepancies }: DiscrepancyTableProps) => {
  const getSeverityBadge = (severity: string) => {
    const config = {
      critical: {
        className: "bg-destructive/10 text-destructive border-destructive/20",
        icon: AlertCircle,
      },
      warning: {
        className: "bg-warning/10 text-warning border-warning/20",
        icon: AlertTriangle,
      },
      clean: {
        className: "bg-success/10 text-success border-success/20",
        icon: CheckCircle,
      },
      info: {
        className: "bg-blue-500/10 text-blue-500 border-blue-500/20",
        icon: AlertCircle,
      }
    };
    return config[severity as keyof typeof config] || config.warning;
  };

  const formatType = (type: string) => {
    if (!type) return "Unknown Discrepancy";
    return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const criticalCount = discrepancies.filter((d) => d.severity === "critical").length;
  const warningCount = discrepancies.filter((d) => d.severity === "warning").length;

  return (
    <Card className="shadow-card animate-slide-in">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <AlertTriangle className="h-5 w-5 text-primary" />
            Discrepancies
          </CardTitle>
          <div className="flex items-center gap-2">
            {criticalCount > 0 && (
              <Badge variant="outline" className="bg-destructive/10 text-destructive border-destructive/20">
                {criticalCount} Critical
              </Badge>
            )}
            {warningCount > 0 && (
              <Badge variant="outline" className="bg-warning/10 text-warning border-warning/20">
                {warningCount} Warning
              </Badge>
            )}
            {criticalCount === 0 && warningCount === 0 && (
              <Badge variant="outline" className="bg-success/10 text-success border-success/20">
                All Clean
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {discrepancies.length === 0 ? (
          <div className="flex items-center justify-center rounded-lg bg-success/5 py-8">
            <div className="text-center">
              <CheckCircle className="mx-auto h-12 w-12 text-success" />
              <p className="mt-2 font-medium text-foreground">No Discrepancies Found</p>
              <p className="text-sm text-muted-foreground">
                Invoice matches purchase order perfectly
              </p>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50 hover:bg-muted/50">
                  <TableHead className="font-semibold">Type</TableHead>
                  <TableHead className="font-semibold">Severity</TableHead>
                  <TableHead className="text-right font-semibold">Confidence</TableHead>
                  <TableHead className="font-semibold">Explanation</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {discrepancies.map((discrepancy, index) => {
                  const severityConfig = getSeverityBadge(discrepancy.severity);
                  const Icon = severityConfig.icon;
                  return (
                    <TableRow
                      key={index}
                      className={index % 2 === 0 ? "bg-background" : "bg-muted/30"}
                    >
                      <TableCell className="font-medium">
                        {formatType(discrepancy.type)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={`capitalize ${severityConfig.className}`}
                        >
                          <Icon className="mr-1 h-3 w-3" />
                          {discrepancy.severity}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <span className="font-medium">{discrepancy.confidence}%</span>
                      </TableCell>
                      <TableCell className="max-w-xs">
                        <p className="truncate text-muted-foreground">
                          {discrepancy.explanation}
                        </p>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DiscrepancyTable;
