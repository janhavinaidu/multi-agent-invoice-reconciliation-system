import { FileText } from "lucide-react";

const Header = () => {
  return (
    <header className="border-b border-border bg-card shadow-soft">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <FileText className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-foreground">
                Invoice Reconciliation Dashboard
              </h1>
              <p className="text-sm text-muted-foreground">
                Multi-Agent AI Powered Invoice Processing
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-success animate-pulse-soft" />
              <span className="text-sm text-muted-foreground">System Online</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
