import { AgentStep } from "@/components/dashboard/StatusStepper";
import { InvoiceData } from "@/components/dashboard/InvoiceDataCard";
import { MatchingResult } from "@/components/dashboard/MatchingResultsCard";
import { Discrepancy } from "@/components/dashboard/DiscrepancyTable";
import { Recommendation } from "@/components/dashboard/RecommendationCard";
import { AgentReasoning } from "@/components/dashboard/AgentTimeline";

export const mockProcessingSteps: AgentStep[] = [
  {
    id: "document",
    name: "Document Intelligence",
    status: "complete",
    confidence: 98,
    executionTime: 1250,
  },
  {
    id: "matching",
    name: "Matching Agent",
    status: "complete",
    confidence: 94,
    executionTime: 890,
  },
  {
    id: "discrepancy",
    name: "Discrepancy Detection",
    status: "complete",
    confidence: 97,
    executionTime: 650,
  },
  {
    id: "resolution",
    name: "Resolution Agent",
    status: "complete",
    confidence: 92,
    executionTime: 420,
  },
];

export const mockInvoiceData: InvoiceData = {
  invoiceNumber: "INV-2024-00847",
  supplier: "Acme Industrial Supplies Co.",
  poReference: "PO-2024-003291",
  totalAmount: 24750.00,
  lineItems: [
    {
      description: "Industrial Grade Steel Bearings (SKU: STL-BRG-100)",
      quantity: 500,
      unitPrice: 24.50,
      total: 12250.00,
    },
    {
      description: "Precision Lubricant - 5L Container (SKU: LUB-PRE-5L)",
      quantity: 100,
      unitPrice: 45.00,
      total: 4500.00,
    },
    {
      description: "Heavy Duty Conveyor Belt - 10m Roll (SKU: CNV-HD-10)",
      quantity: 20,
      unitPrice: 320.00,
      total: 6400.00,
    },
    {
      description: "Safety Equipment Kit - Standard (SKU: SAF-STD-KIT)",
      quantity: 16,
      unitPrice: 100.00,
      total: 1600.00,
    },
  ],
};

export const mockMatchingResult: MatchingResult = {
  matchType: "fuzzy",
  confidence: 94,
  matchedPoId: "PO-2024-003291",
  matchedItems: [
    "Industrial Grade Steel Bearings (500 units)",
    "Precision Lubricant - 5L Container (100 units)",
    "Heavy Duty Conveyor Belt - 10m Roll (20 units)",
  ],
  unmatchedItems: ["Safety Equipment Kit - Standard (16 units)"],
};

export const mockDiscrepancies: Discrepancy[] = [
  {
    type: "price",
    severity: "warning",
    confidence: 96,
    explanation:
      "Unit price for Steel Bearings differs from PO. Invoice: $24.50, PO: $23.75. Difference: $0.75/unit ($375 total variance)",
    field: "unit_price",
    expectedValue: "$23.75",
    actualValue: "$24.50",
  },
  {
    type: "missing_po",
    severity: "critical",
    confidence: 99,
    explanation:
      "Safety Equipment Kit (16 units @ $100) not found in original Purchase Order. Requires verification.",
    field: "line_item",
    expectedValue: "Not in PO",
    actualValue: "$1,600.00",
  },
  {
    type: "quantity",
    severity: "warning",
    confidence: 89,
    explanation:
      "Conveyor Belt quantity slightly differs. Invoice: 20 rolls, PO: 18 rolls. 2 additional units added.",
    field: "quantity",
    expectedValue: "18",
    actualValue: "20",
  },
];

export const mockRecommendation: Recommendation = {
  decision: "request_clarification",
  riskLevel: "medium",
  financialImpact: 2615,
  reasoning:
    "Invoice contains one unauthorized line item (Safety Equipment Kit - $1,600) and two price/quantity variances totaling $1,015. The unauthorized item requires purchase approval. Price variance on Steel Bearings may be due to market fluctuation. Recommend obtaining clarification before payment processing.",
  suggestedSteps: [
    "Verify Safety Equipment Kit purchase with requesting department",
    "Confirm price increase on Steel Bearings with supplier",
    "Request updated PO to include additional conveyor belt units",
    "Once verified, resubmit for auto-approval",
  ],
};

export const mockAgentReasoning: AgentReasoning[] = [
  {
    id: "document_intelligence",
    agentName: "Document Intelligence Agent",
    reasoning:
      "Successfully extracted invoice data using OCR and NLP. Detected 4 line items with high confidence. Invoice format matches standard commercial invoice template. Currency: USD. Tax status: Exempt. Payment terms: Net 30.",
    confidence: 98,
    executionTime: 1250,
    timestamp: "10:23:15 AM",
  },
  {
    id: "matching_agent",
    agentName: "Matching Agent",
    reasoning:
      "Performed fuzzy matching against PO database. Found primary match PO-2024-003291 with 94% confidence using semantic similarity on supplier name and line item descriptions. 3 of 4 items successfully matched. SKU codes aligned with catalog database.",
    confidence: 94,
    executionTime: 890,
    timestamp: "10:23:17 AM",
  },
  {
    id: "discrepancy_agent",
    agentName: "Discrepancy Detection Agent",
    reasoning:
      "Identified 3 discrepancies: 1 critical (unauthorized item), 2 warnings (price/quantity variance). Total financial impact calculated at $2,615. Cross-referenced historical pricing data - Steel Bearing price increase aligns with Q4 market trends (+3.2%).",
    confidence: 97,
    executionTime: 650,
    timestamp: "10:23:18 AM",
  },
  {
    id: "resolution_agent",
    agentName: "Resolution Agent",
    reasoning:
      "Based on discrepancy analysis and company policy thresholds, recommending 'Request Clarification' action. Unauthorized line item exceeds auto-approval threshold ($500). Risk score: Medium (42/100). Suggested resolution path generated with 4 action items.",
    confidence: 92,
    executionTime: 420,
    timestamp: "10:23:18 AM",
  },
];

// Initial pending state for steps
export const initialProcessingSteps: AgentStep[] = [
  { id: "document", name: "Document Intelligence", status: "pending" },
  { id: "matching", name: "Matching Agent", status: "pending" },
  { id: "discrepancy", name: "Discrepancy Detection", status: "pending" },
  { id: "resolution", name: "Resolution Agent", status: "pending" },
];
