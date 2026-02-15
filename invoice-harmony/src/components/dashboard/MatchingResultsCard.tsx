import { GitCompare, Check, X, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface MatchingResult {
  matchType: "exact" | "fuzzy" | "semantic";
  confidence: number;
  matchedPoId: string;
  matchedItems: string[];
  unmatchedItems: string[];
}

interface MatchingResultsCardProps {
  data: MatchingResult;
}

const MatchingResultsCard = ({ data }: MatchingResultsCardProps) => {
  const getMatchTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      exact: "bg-success/10 text-success border-success/20",
      fuzzy: "bg-warning/10 text-warning border-warning/20",
      semantic: "bg-primary/10 text-primary border-primary/20",
      none: "bg-muted text-muted-foreground border-border",
    };
    return styles[type as keyof typeof styles] || styles.none;
  };

  return (
    <Card className="shadow-card animate-slide-in">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <GitCompare className="h-5 w-5 text-primary" />
          Matching Results
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Matching Info */}
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg bg-muted/50 p-4">
              <p className="text-sm text-muted-foreground">Match Type</p>
              <div className="mt-2">
                <Badge
                  variant="outline"
                  className={`text-sm capitalize ${getMatchTypeBadge(data.matchType)}`}
                >
                  {data.matchType}
                </Badge>
              </div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4">
              <p className="text-sm text-muted-foreground">Confidence Score</p>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="text-2xl font-bold text-foreground">
                  {data.confidence}%
                </span>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-border">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${data.confidence}%` }}
                />
              </div>
            </div>
            <div className="rounded-lg bg-muted/50 p-4">
              <p className="text-sm text-muted-foreground">Matched PO ID</p>
              <p className="mt-1 text-lg font-semibold text-foreground">
                {data.matchedPoId}
              </p>
            </div>
          </div>

          {/* Matched Items */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-success/20 bg-success/5 p-4">
              <div className="mb-3 flex items-center gap-2">
                <Check className="h-4 w-4 text-success" />
                <h4 className="font-medium text-foreground">
                  Matched Items ({data.matchedItems.length})
                </h4>
              </div>
              <ul className="space-y-2">
                {data.matchedItems.map((item, index) => (
                  <li
                    key={index}
                    className="flex items-center gap-2 text-sm text-foreground"
                  >
                    <Check className="h-3 w-3 text-success" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
              <div className="mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <h4 className="font-medium text-foreground">
                  Unmatched Items ({data.unmatchedItems.length})
                </h4>
              </div>
              {data.unmatchedItems.length > 0 ? (
                <ul className="space-y-2">
                  {data.unmatchedItems.map((item, index) => (
                    <li
                      key={index}
                      className="flex items-center gap-2 text-sm text-foreground"
                    >
                      <X className="h-3 w-3 text-destructive" />
                      {item}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">
                  All items successfully matched
                </p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MatchingResultsCard;
