import { Check, Loader2, Clock, Brain, GitCompare, AlertTriangle, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface AgentStep {
  id: string;
  name: string;
  status: "pending" | "running" | "complete";
  confidence?: number;
  executionTime?: number;
}

interface StatusStepperProps {
  steps: AgentStep[];
}

const agentIcons: Record<string, React.ElementType> = {
  document: Brain,
  matching: GitCompare,
  discrepancy: AlertTriangle,
  resolution: Shield,
};

const StatusStepper = ({ steps }: StatusStepperProps) => {
  const getStatusIcon = (status: AgentStep["status"], id: string) => {
    if (status === "complete") {
      return <Check className="h-4 w-4 text-success-foreground" />;
    }
    if (status === "running") {
      return <Loader2 className="h-4 w-4 animate-spin text-primary-foreground" />;
    }
    const Icon = agentIcons[id] || Clock;
    return <Icon className="h-4 w-4 text-muted-foreground" />;
  };

  const getStatusStyles = (status: AgentStep["status"]) => {
    if (status === "complete") {
      return "bg-success border-success";
    }
    if (status === "running") {
      return "bg-primary border-primary";
    }
    return "bg-muted border-border";
  };

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Clock className="h-5 w-5 text-primary" />
          Processing Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={step.id} className="relative">
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={`absolute left-5 top-10 h-8 w-0.5 ${
                    step.status === "complete" ? "bg-success" : "bg-border"
                  }`}
                />
              )}

              <div className="flex items-start gap-4">
                {/* Status icon */}
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 transition-all ${getStatusStyles(
                    step.status
                  )}`}
                >
                  {getStatusIcon(step.status, step.id)}
                </div>

                {/* Step content */}
                <div className="flex-1 pt-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-foreground">{step.name}</h4>
                    {step.status === "running" && (
                      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        Running
                      </span>
                    )}
                    {step.status === "complete" && (
                      <span className="rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
                        Complete
                      </span>
                    )}
                    {step.status === "pending" && (
                      <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        Pending
                      </span>
                    )}
                  </div>

                  {step.status === "complete" && (
                    <div className="mt-1 flex items-center gap-4 text-sm text-muted-foreground">
                      {step.confidence !== undefined && (
                        <span>
                          Confidence:{" "}
                          <span className="font-medium text-foreground">
                            {step.confidence}%
                          </span>
                        </span>
                      )}
                      {step.executionTime !== undefined && (
                        <span>
                          Time:{" "}
                          <span className="font-medium text-foreground">
                            {step.executionTime}ms
                          </span>
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default StatusStepper;
