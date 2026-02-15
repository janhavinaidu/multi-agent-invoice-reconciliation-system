import { useState } from "react";
import { ChevronDown, ChevronUp, Brain, GitCompare, AlertTriangle, Shield, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";

export interface AgentReasoning {
  id: string;
  agentName: string;
  reasoning: string;
  confidence: number;
  executionTime: number;
  timestamp: string;
}

interface AgentTimelineProps {
  agents: AgentReasoning[];
}

const agentIcons: Record<string, React.ElementType> = {
  document_intelligence: Brain,
  matching: GitCompare,
  discrepancy_detection: AlertTriangle,
  resolution: Shield,
};

const agentColors: Record<string, string> = {
  document_intelligence: "bg-blue-500",
  matching: "bg-purple-500",
  discrepancy_detection: "bg-amber-500",
  resolution: "bg-emerald-500",
};

const AgentTimeline = ({ agents }: AgentTimelineProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card className="shadow-card animate-slide-in">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer transition-colors hover:bg-muted/50">
            <CardTitle className="flex items-center justify-between text-lg">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                Agent Reasoning Timeline
              </div>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                {isOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </CardTitle>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent className="pt-0">
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-5 top-0 h-full w-0.5 bg-border" />

              <div className="space-y-6">
                {agents.map((agent, index) => {
                  const Icon = agentIcons[agent.id] || Brain;
                  const colorClass = agentColors[agent.id] || "bg-primary";

                  return (
                    <div key={agent.id} className="relative pl-14">
                      {/* Timeline dot */}
                      <div
                        className={`absolute left-3 top-1 flex h-5 w-5 items-center justify-center rounded-full ${colorClass}`}
                      >
                        <Icon className="h-3 w-3 text-white" />
                      </div>

                      {/* Content */}
                      <div className="rounded-lg border bg-card p-4 shadow-soft">
                        <div className="mb-2 flex items-center justify-between">
                          <h4 className="font-semibold text-foreground">
                            {agent.agentName}
                          </h4>
                          <span className="text-xs text-muted-foreground">
                            {agent.timestamp}
                          </span>
                        </div>

                        <p className="mb-3 text-sm text-muted-foreground leading-relaxed">
                          {agent.reasoning}
                        </p>

                        <div className="flex items-center gap-4 text-xs">
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <div className="h-1.5 w-1.5 rounded-full bg-success" />
                            Confidence:{" "}
                            <span className="font-medium text-foreground">
                              {agent.confidence}%
                            </span>
                          </div>
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            {agent.executionTime}ms
                          </div>
                        </div>
                      </div>

                      {/* Connector arrow */}
                      {index < agents.length - 1 && (
                        <div className="absolute left-5 top-full flex h-6 -translate-x-1/2 items-center justify-center">
                          <ChevronDown className="h-4 w-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
};

export default AgentTimeline;
