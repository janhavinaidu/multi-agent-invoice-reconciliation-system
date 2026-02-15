import { Shield, CheckCircle, AlertCircle, AlertTriangle, Download, UserCheck, ThumbsUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export interface Recommendation {
  decision: "auto_approve" | "request_clarification" | "escalate" | "escalate_to_human" | "unapproved" | "pending";
  riskLevel: "high" | "medium" | "low";
  financialImpact: number;
  suggestedSteps: string[];
  reasoning: string;
  summary?: string;
}

interface RecommendationCardProps {
  recommendation: Recommendation;
  onApprove: () => void;
  onUnapprove: () => void;
  onEscalate: () => void;
  onDownload: () => void;
}

const RecommendationCard = ({
  recommendation,
  onApprove,
  onUnapprove,
  onEscalate,
  onDownload,
}: RecommendationCardProps) => {
  const getDecisionConfig = (decision: string) => {
    const config = {
      auto_approve: {
        label: "Auto Approve",
        icon: ThumbsUp,
        className: "bg-success/10 border-success/30 text-success",
        bgClass: "bg-success/5",
      },
      unapproved: {
        label: "Unapproved",
        icon: AlertCircle,
        className: "bg-destructive/10 border-destructive/30 text-destructive",
        bgClass: "bg-destructive/5",
      },
      pending: {
        label: "Pending Verification",
        icon: AlertTriangle,
        className: "bg-warning/10 border-warning/30 text-warning",
        bgClass: "bg-warning/5",
      },
      request_clarification: {
        label: "Request Clarification",
        icon: AlertTriangle,
        className: "bg-warning/10 border-warning/30 text-warning",
        bgClass: "bg-warning/5",
      },
      escalate: {
        label: "Escalate to Manager",
        icon: UserCheck,
        className: "bg-destructive/10 border-destructive/30 text-destructive",
        bgClass: "bg-destructive/5",
      },
      escalate_to_human: {
        label: "Escalate to Human",
        icon: AlertCircle,
        className: "bg-destructive/10 border-destructive/30 text-destructive",
        bgClass: "bg-destructive/5",
      }
    };
    return config[decision as keyof typeof config] || config.request_clarification;
  };

  const getRiskConfig = (risk: string) => {
    const config = {
      low: "bg-success/10 text-success border-success/20",
      medium: "bg-warning/10 text-warning border-warning/20",
      high: "bg-destructive/10 text-destructive border-destructive/20",
    };
    return config[risk as keyof typeof config] || config.medium;
  };

  const decisionConfig = getDecisionConfig(recommendation.decision);
  const DecisionIcon = decisionConfig.icon;

  return (
    <Card className="shadow-card animate-slide-in overflow-hidden">
      <CardHeader className={decisionConfig.bgClass}>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Shield className="h-5 w-5 text-primary" />
          Resolution Recommendation
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        {/* Main Decision Box */}
        <div
          className={`mb-6 rounded-xl border-2 p-6 ${decisionConfig.className}`}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-card">
              <DecisionIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-medium opacity-80">Final Decision</p>
              <h3 className="text-2xl font-bold">{decisionConfig.label}</h3>
            </div>
          </div>
        </div>

        {/* Priority Summary */}
        {recommendation.summary && (
          <div className="mb-6 rounded-lg bg-primary/5 border border-primary/20 p-4">
            <p className="mb-1 text-sm font-semibold text-primary">Summary</p>
            <p className="text-sm text-foreground">{recommendation.summary}</p>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="mb-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg bg-muted/50 p-4">
            <p className="text-sm text-muted-foreground">Risk Level</p>
            <div className="mt-2">
              <Badge
                variant="outline"
                className={`text-sm capitalize ${getRiskConfig(recommendation.riskLevel)}`}
              >
                {recommendation.riskLevel} Risk
              </Badge>
            </div>
          </div>
          <div className="rounded-lg bg-muted/50 p-4">
            <p className="text-sm text-muted-foreground">Financial Impact</p>
            <p className="mt-1 text-2xl font-bold text-foreground">
              ${recommendation.financialImpact.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Reasoning */}
        <div className="mb-6 rounded-lg bg-muted/50 p-4">
          <p className="mb-2 text-sm font-medium text-foreground">AI Reasoning</p>
          <p className="text-sm text-muted-foreground">{recommendation.reasoning}</p>
        </div>

        {/* Suggested Steps */}
        <div className="mb-6">
          <p className="mb-3 text-sm font-medium text-foreground">Suggested Next Steps</p>
          <ul className="space-y-2">
            {recommendation.suggestedSteps.map((step, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                  {index + 1}
                </span>
                {step}
              </li>
            ))}
          </ul>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3">
          <Button onClick={onApprove} className="flex-1 sm:flex-none">
            <ThumbsUp className="mr-2 h-4 w-4" />
            Approve
          </Button>
          <Button onClick={onUnapprove} variant="destructive" className="flex-1 sm:flex-none">
            <AlertCircle className="mr-2 h-4 w-4" />
            Unapprove
          </Button>
          <Button onClick={onEscalate} variant="outline" className="flex-1 sm:flex-none">
            <UserCheck className="mr-2 h-4 w-4" />
            Escalate to Human
          </Button>
          <Button onClick={onDownload} variant="outline" className="flex-1 sm:flex-none">
            <Download className="mr-2 h-4 w-4" />
            Download Report
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default RecommendationCard;
