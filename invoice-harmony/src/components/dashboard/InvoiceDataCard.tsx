import { FileText, Building2, Hash, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export interface LineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface InvoiceData {
  invoiceNumber: string;
  supplier: string;
  poReference: string;
  totalAmount: number;
  lineItems: LineItem[];
}

interface InvoiceDataCardProps {
  data: InvoiceData;
}

const InvoiceDataCard = ({ data }: InvoiceDataCardProps) => {
  return (
    <Card className="shadow-card animate-slide-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <FileText className="h-5 w-5 text-primary" />
          Extracted Invoice Data
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Invoice Metadata */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg bg-muted/50 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Hash className="h-4 w-4" />
              Invoice Number
            </div>
            <p className="mt-1 text-lg font-semibold text-foreground">
              {data.invoiceNumber}
            </p>
          </div>
          <div className="rounded-lg bg-muted/50 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Building2 className="h-4 w-4" />
              Supplier
            </div>
            <p className="mt-1 text-lg font-semibold text-foreground">
              {data.supplier}
            </p>
          </div>
          <div className="rounded-lg bg-muted/50 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FileText className="h-4 w-4" />
              PO Reference
            </div>
            <p className="mt-1 text-sm font-semibold text-foreground truncate" title={data.poReference}>
              {data.poReference}
            </p>
          </div>
          <div className="rounded-lg bg-muted/50 p-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <DollarSign className="h-4 w-4" />
              Total Amount
            </div>
            <p className="mt-1 text-lg font-semibold text-foreground">
              ${(data.totalAmount || 0).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Line Items Table */}
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50 hover:bg-muted/50">
                <TableHead className="font-semibold">Description</TableHead>
                <TableHead className="text-right font-semibold">Qty</TableHead>
                <TableHead className="text-right font-semibold">Unit Price</TableHead>
                <TableHead className="text-right font-semibold">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(data.lineItems || []).map((item, index) => (
                <TableRow
                  key={index}
                  className={index % 2 === 0 ? "bg-background" : "bg-muted/30"}
                >
                  <TableCell className="font-medium">{item.description || "No description"}</TableCell>
                  <TableCell className="text-right">{item.quantity || 0}</TableCell>
                  <TableCell className="text-right">
                    ${(item.unitPrice || 0).toFixed(2)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    ${(item.total || 0).toFixed(2)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default InvoiceDataCard;
