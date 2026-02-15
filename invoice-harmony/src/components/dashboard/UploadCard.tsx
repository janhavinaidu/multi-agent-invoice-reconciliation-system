import { useState, useCallback } from "react";
import { Upload, FileText, FileJson, X, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface UploadCardProps {
  onProcess: (invoice: File, po: File | null) => void;
  isProcessing: boolean;
}

const UploadCard = ({ onProcess, isProcessing }: UploadCardProps) => {
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null);
  const [poFile, setPoFile] = useState<File | null>(null);
  const [invoiceDragActive, setInvoiceDragActive] = useState(false);
  const [poDragActive, setPoDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDrag = useCallback(
    (e: React.DragEvent, setter: (val: boolean) => void, active: boolean) => {
      e.preventDefault();
      e.stopPropagation();
      setter(active);
    },
    []
  );

  const handleInvoiceDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setInvoiceDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setInvoiceFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handlePoDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setPoDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setPoFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleProcess = () => {
    setUploadProgress(0);
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 100);
    onProcess(invoiceFile!, poFile);
  };

  const canProcess = invoiceFile && !isProcessing;

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Upload className="h-5 w-5 text-primary" />
          Upload Documents
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Invoice Upload */}
        <div>
          <label className="mb-2 block text-sm font-medium text-foreground">
            Invoice (PDF/Image)
          </label>
          <div
            className={`relative rounded-lg border-2 border-dashed p-6 text-center transition-colors ${invoiceDragActive
              ? "border-primary bg-primary/5"
              : invoiceFile
                ? "border-success bg-success/5"
                : "border-border hover:border-primary/50"
              }`}
            onDragEnter={(e) => handleDrag(e, setInvoiceDragActive, true)}
            onDragLeave={(e) => handleDrag(e, setInvoiceDragActive, false)}
            onDragOver={(e) => handleDrag(e, setInvoiceDragActive, true)}
            onDrop={handleInvoiceDrop}
          >
            {invoiceFile ? (
              <div className="flex items-center justify-center gap-2">
                <FileText className="h-5 w-5 text-success" />
                <span className="text-sm font-medium text-foreground">
                  {invoiceFile.name}
                </span>
                <button
                  onClick={() => setInvoiceFile(null)}
                  className="ml-2 rounded-full p-1 hover:bg-muted"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
            ) : (
              <>
                <FileText className="mx-auto h-8 w-8 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  Drag & drop invoice or{" "}
                  <label className="cursor-pointer font-medium text-primary hover:underline">
                    browse
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={(e) =>
                        e.target.files && setInvoiceFile(e.target.files[0])
                      }
                    />
                  </label>
                </p>
              </>
            )}
          </div>
        </div>

        {/* PO Upload */}
        <div>
          <label className="mb-2 block text-sm font-medium text-foreground">
            Purchase Order (JSON/PDF) <span className="text-muted-foreground">(Optional)</span>
          </label>
          <div
            className={`relative rounded-lg border-2 border-dashed p-6 text-center transition-colors ${poDragActive
              ? "border-primary bg-primary/5"
              : poFile
                ? "border-success bg-success/5"
                : "border-border hover:border-primary/50"
              }`}
            onDragEnter={(e) => handleDrag(e, setPoDragActive, true)}
            onDragLeave={(e) => handleDrag(e, setPoDragActive, false)}
            onDragOver={(e) => handleDrag(e, setPoDragActive, true)}
            onDrop={handlePoDrop}
          >
            {poFile ? (
              <div className="flex items-center justify-center gap-2">
                <FileJson className="h-5 w-5 text-success" />
                <span className="text-sm font-medium text-foreground">
                  {poFile.name}
                </span>
                <button
                  onClick={() => setPoFile(null)}
                  className="ml-2 rounded-full p-1 hover:bg-muted"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
              </div>
            ) : (
              <>
                <FileJson className="mx-auto h-8 w-8 text-muted-foreground" />
                <p className="mt-2 text-sm text-muted-foreground">
                  Drag & drop PO file or{" "}
                  <label className="cursor-pointer font-medium text-primary hover:underline">
                    browse
                    <input
                      type="file"
                      className="hidden"
                      accept=".json,.pdf"
                      onChange={(e) =>
                        e.target.files && setPoFile(e.target.files[0])
                      }
                    />
                  </label>
                </p>
              </>
            )}
          </div>
        </div>

        {/* Upload Progress */}
        {isProcessing && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Uploading documents...</span>
              <span className="font-medium text-foreground">{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
          </div>
        )}

        {/* Process Button */}
        <div className="space-y-2">
          <Button
            onClick={handleProcess}
            disabled={!canProcess}
            className="w-full"
            size="lg"
          >
            {isProcessing ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Process Invoice
              </>
            )}
          </Button>

          {/* Helper text when button is disabled */}
          {!canProcess && !isProcessing && (
            <p className="text-center text-sm text-muted-foreground">
              Upload an invoice to continue
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default UploadCard;
