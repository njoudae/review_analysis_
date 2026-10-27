import { notFound } from "next/navigation";
import { PageHeader } from "@/components/page-header";
import { MetricCard } from "@/components/metric-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch } from "@/lib/api";
import { label, statusTone } from "@/lib/labels";
import { resolveRange } from "@/lib/range";
import type { Branch, Employee, ReviewPage, Summary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default async function BranchDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let branch: Branch;
  try { branch = await backendFetch<Branch>(`/branches/${id}`); } catch { notFound(); }
  const { startDate, endDate } = resolveRange("30d");
  const [summary, employees, reviews] = await Promise.all([
    backendFetch<Summary>(`/dashboard/summary?organization_id=${branch.organization_id}&branch_id=${id}&start_date=${startDate}&end_date=${endDate}`),
    backendFetch<Employee[]>(`/employees?organization_id=${branch.organization_id}&branch_id=${id}`),
    backendFetch<ReviewPage>(`/reviews?organization_id=${branch.organization_id}&branch_id=${id}&page_size=10`),
  ]);
  return <><PageHeader title={branch.name} description={`${branch.city}${branch.district ? ` — ${branch.district}` : ""}`} actions={<><Badge tone={statusTone(branch.status)}>{label(branch.status)}</Badge><a className="button button-secondary" href={branch.google_maps_url} target="_blank" rel="noreferrer">Google Maps</a></>} /><div className="metric-grid"><MetricCard label="الموظفون" value={employees.length}/><MetricCard label="المراجعات" value={summary.total_reviews}/><MetricCard label="الإيجابية" value={summary.positive_reviews}/><MetricCard label="السلبية" value={summary.negative_reviews}/><MetricCard label="متوسط التقييم" value={summary.average_rating} digits={2}/><MetricCard label="مشكلات مفتوحة" value={summary.unresolved_issues}/></div><Card className="section-space"><CardHeader><CardTitle>آخر المراجعات</CardTitle></CardHeader><CardContent>{reviews.items.length ? <Table><TableHeader><TableRow><TableHead>المراجع</TableHead><TableHead>التقييم</TableHead><TableHead>النص</TableHead><TableHead>المشاعر</TableHead><TableHead>التاريخ</TableHead></TableRow></TableHeader><TableBody>{reviews.items.map((review) => <TableRow key={review.id}><TableCell>{review.reviewer_name ?? "مراجع مجهول"}</TableCell><TableCell>{review.rating ?? "—"}</TableCell><TableCell className="review-excerpt" title={review.review_text}>{review.review_text || "دون نص"}</TableCell><TableCell><Badge tone={review.analysis?.sentiment === "negative" ? "danger" : review.analysis?.sentiment === "positive" ? "success" : "neutral"}>{label(review.analysis?.sentiment)}</Badge></TableCell><TableCell>{formatDate(review.published_at)}</TableCell></TableRow>)}</TableBody></Table> : <div className="chart-empty">لا توجد مراجعات لهذا الفرع.</div>}</CardContent></Card><Card className="section-space"><CardHeader><CardTitle>الموظفون</CardTitle></CardHeader><CardContent>{employees.length ? <Table><TableHeader><TableRow><TableHead>الموظف</TableHead><TableHead>الجنس</TableHead><TableHead>الدور</TableHead><TableHead>الجنسية</TableHead></TableRow></TableHeader><TableBody>{employees.map((employee) => <TableRow key={employee.id}><TableCell>{employee.first_name} {employee.last_name}</TableCell><TableCell>{label(employee.gender)}</TableCell><TableCell>{employee.job_title}</TableCell><TableCell>{employee.nationality}</TableCell></TableRow>)}</TableBody></Table> : <div className="chart-empty">لم تتم إضافة موظفين.</div>}</CardContent></Card></>;
}

