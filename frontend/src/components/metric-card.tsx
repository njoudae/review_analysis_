import { ArrowDownLeft, ArrowUpLeft, Minus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";

export function MetricCard({ label, value, comparison, digits = 0 }: { label: string; value: number | null; comparison?: number | null; digits?: number }) {
  const good = comparison != null && comparison > 0;
  const bad = comparison != null && comparison < 0;
  return <Card className="metric-card"><CardContent><span>{label}</span><strong>{formatNumber(value, digits)}</strong><small className={good ? "delta-up" : bad ? "delta-down" : "delta-neutral"}>{good ? <ArrowUpLeft /> : bad ? <ArrowDownLeft /> : <Minus />}{comparison == null ? "لا تتوفر مقارنة" : `${Math.abs(comparison)}% عن الفترة السابقة`}</small></CardContent></Card>;
}

