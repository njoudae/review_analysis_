import Link from "next/link";
import { AlertTriangle, ArrowUpLeft } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { MetricCard } from "@/components/metric-card";
import { PageHeader } from "@/components/page-header";
import { SentimentChart } from "@/components/sentiment-chart";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch, getOrganization } from "@/lib/api";
import { label, statusTone } from "@/lib/labels";
import { resolveRange } from "@/lib/range";
import type { Branch, BranchPerformance, Issue, Summary } from "@/lib/types";
import { formatNumber } from "@/lib/utils";

export default async function DashboardPage({ searchParams }: { searchParams: Promise<{ range?: string; branch?: string }> }) {
  const query = await searchParams;
  const organization = await getOrganization();
  if (!organization) return <><PageHeader title="لوحة القيادة" description="ملخص تنفيذي لتجربة العملاء" /><EmptyState title="ابدأ بإعداد المؤسسة" description="لا توجد مؤسسة في قاعدة البيانات بعد. أضف بيانات المؤسسة ثم الفروع لبدء جمع المراجعات." href="/settings" action="إعداد المؤسسة" /></>;
  const range = query.range ?? "30d";
  const { startDate, endDate } = resolveRange(range);
  const branchParam = query.branch ? `&branch_id=${query.branch}` : "";
  const common = `organization_id=${organization.id}&start_date=${startDate}&end_date=${endDate}`;
  const [summary, branches, performance, issues] = await Promise.all([
    backendFetch<Summary>(`/dashboard/summary?${common}${branchParam}`),
    backendFetch<Branch[]>(`/branches?organization_id=${organization.id}`),
    backendFetch<BranchPerformance[]>(`/dashboard/branches?${common}`),
    backendFetch<Issue[]>(`/issues?organization_id=${organization.id}`),
  ]);
  const maxComplaint = Math.max(...summary.top_complaints.map((item) => item.count), 1);
  const attention = issues.filter((item) => ["critical", "high"].includes(item.severity) && !["RESOLVED", "DISMISSED"].includes(item.status)).slice(0, 5);
  return <>
    <PageHeader title={organization.name} description={`متابعة تجربة العملاء — ${organization.city}`} actions={<Badge tone="success">بيانات مباشرة من قاعدة البيانات</Badge>} />
    <form className="filter-bar" method="get"><div className="field"><label htmlFor="range">الفترة</label><select className="select" id="range" name="range" defaultValue={range}><option value="today">اليوم</option><option value="7d">7 أيام</option><option value="30d">30 يومًا</option><option value="3m">3 أشهر</option></select></div><div className="field"><label htmlFor="branch">الفرع</label><select className="select" id="branch" name="branch" defaultValue={query.branch ?? ""}><option value="">كل الفروع</option>{branches.map((branch) => <option value={branch.id} key={branch.id}>{branch.name}</option>)}</select></div><div className="field" style={{ alignSelf: "end" }}><button className="button button-secondary" type="submit">تطبيق الفلاتر</button></div></form>
    <div className="metric-grid"><MetricCard label="إجمالي الفروع" value={summary.total_branches} /><MetricCard label="المراجعون" value={summary.total_reviewers} comparison={summary.comparisons.total_reviewers} /><MetricCard label="المراجعات" value={summary.total_reviews} comparison={summary.comparisons.total_reviews} /><MetricCard label="الإيجابية" value={summary.positive_reviews} comparison={summary.comparisons.positive_reviews} /><MetricCard label="السلبية" value={summary.negative_reviews} comparison={summary.comparisons.negative_reviews} /><MetricCard label="متوسط التقييم" value={summary.average_rating} comparison={summary.comparisons.average_rating} digits={2} /></div>
    <div className="dashboard-grid"><Card><CardHeader><CardTitle>اتجاه المشاعر</CardTitle><span className="cell-muted">حسب تاريخ نشر المراجعة</span></CardHeader><CardContent><SentimentChart data={summary.sentiment_trend} /></CardContent></Card><Card><CardHeader><CardTitle>أكثر فئات الشكاوى</CardTitle></CardHeader><CardContent className="complaint-list">{summary.top_complaints.length ? summary.top_complaints.map((item) => <div className="complaint-row" key={item.category}><div className="complaint-meta"><span>{item.category}</span><strong>{formatNumber(item.count)}</strong></div><div className="bar-track"><div className="bar-fill" style={{ width: `${(item.count / maxComplaint) * 100}%` }} /></div></div>) : <div className="chart-empty">لا توجد شكاوى مصنفة.</div>}</CardContent></Card></div>
    <Card className="section-space"><CardHeader><CardTitle>أداء الفروع</CardTitle><Link className="cell-muted" href="/branches">عرض كل الفروع <ArrowUpLeft size={13} /></Link></CardHeader><CardContent><Table><TableHeader><TableRow><TableHead>الفرع</TableHead><TableHead>الموظفون</TableHead><TableHead>المراجعات</TableHead><TableHead>إيجابية</TableHead><TableHead>سلبية</TableHead><TableHead>متوسط التقييم</TableHead><TableHead>مشكلات مفتوحة</TableHead></TableRow></TableHeader><TableBody>{performance.map((item) => <TableRow key={item.id}><TableCell><Link className="cell-title" href={`/branches/${item.id}`}>{item.branch}</Link><div className="cell-muted">{item.city}</div></TableCell><TableCell>{item.employee_count}</TableCell><TableCell>{item.total_reviews}</TableCell><TableCell>{item.positive_reviews}</TableCell><TableCell>{item.negative_reviews}</TableCell><TableCell>{formatNumber(item.average_rating, 2)}</TableCell><TableCell><Badge tone={item.open_issues ? "warning" : "success"}>{item.open_issues}</Badge></TableCell></TableRow>)}</TableBody></Table></CardContent></Card>
    <Card className="section-space"><CardHeader><CardTitle>تحتاج انتباهًا</CardTitle><Badge tone={summary.unresolved_issues ? "warning" : "success"}>{summary.unresolved_issues} غير محلولة</Badge></CardHeader><CardContent>{attention.length ? <Table><TableHeader><TableRow><TableHead>الملخص</TableHead><TableHead>الفئة</TableHead><TableHead>الخطورة</TableHead><TableHead>الحالة</TableHead></TableRow></TableHeader><TableBody>{attention.map((issue) => <TableRow key={issue.id}><TableCell className="issue-summary"><AlertTriangle size={14} aria-hidden="true" /> {issue.summary}</TableCell><TableCell>{issue.category}</TableCell><TableCell><Badge tone={statusTone(issue.severity)}>{label(issue.severity)}</Badge></TableCell><TableCell><Badge tone={statusTone(issue.status)}>{label(issue.status)}</Badge></TableCell></TableRow>)}</TableBody></Table> : <div className="chart-empty">لا توجد مشكلات مرتفعة أو حرجة مفتوحة.</div>}</CardContent></Card>
  </>;
}

