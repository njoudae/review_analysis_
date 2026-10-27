export function statusTone(value: string): "neutral" | "success" | "warning" | "danger" | "info" {
  if (["active", "COMPLETED", "SENT", "RESOLVED"].includes(value)) return "success";
  if (["FAILED", "FAILED_ANALYSIS", "critical", "high"].includes(value)) return "danger";
  if (["medium", "ACTION_REQUIRED", "SENDING_REPORT", "ANALYZING"].includes(value)) return "warning";
  if (["STARTED", "COLLECTING", "NEW", "REVIEWING"].includes(value)) return "info";
  return "neutral";
}

export const labels: Record<string, string> = {
  active: "نشط", inactive: "غير نشط", positive: "إيجابية", negative: "سلبية", neutral: "محايدة", mixed: "مختلطة",
  low: "منخفضة", medium: "متوسطة", high: "مرتفعة", critical: "حرجة", F: "أنثى", M: "ذكر",
  STARTED: "بانتظار العامل", COLLECTING: "جمع المراجعات", ANALYZING: "قيد التحليل", GENERATING_REPORT: "إنشاء التقرير",
  SENDING_REPORT: "إرسال التقرير", COMPLETED: "مكتمل", FAILED: "فشل", NEW: "جديدة", REVIEWING: "مراجعة",
  INVESTIGATING: "تحقيق", ACTION_REQUIRED: "إجراء مطلوب", RESOLVED: "محلولة", DISMISSED: "مستبعدة",
};

export function label(value: string | undefined | null) { return value ? labels[value] ?? value : "—"; }

