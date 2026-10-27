import { updateIssue } from "@/app/actions";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch, getOrganization } from "@/lib/api";
import { label, statusTone } from "@/lib/labels";
import type { Branch, Issue } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default async function IssuesPage() {
  const organization = await getOrganization();
  if (!organization) return <EmptyState title="لا توجد مؤسسة" description="أضف المؤسسة أولًا." href="/settings" action="إعداد المؤسسة" />;
  const [issues, branches] = await Promise.all([backendFetch<Issue[]>(`/issues?organization_id=${organization.id}`), backendFetch<Branch[]>(`/branches?organization_id=${organization.id}`)]);
  const branchMap = new Map(branches.map((branch) => [branch.id, branch.name]));
  return <><PageHeader title="المشكلات التشغيلية" description="تحقيق، إسناد، وإغلاق المشكلات المستخرجة من المراجعات" /><Card><CardContent>{issues.length ? <Table><TableHeader><TableRow><TableHead>الملخص</TableHead><TableHead>الفرع</TableHead><TableHead>الفئة</TableHead><TableHead>الخطورة</TableHead><TableHead>الحالة</TableHead><TableHead>التاريخ</TableHead><TableHead>تحديث</TableHead></TableRow></TableHeader><TableBody>{issues.map((issue) => <TableRow key={issue.id}><TableCell className="issue-summary">{issue.summary}</TableCell><TableCell>{branchMap.get(issue.branch_id) ?? "—"}</TableCell><TableCell>{issue.category}<div className="cell-muted">{issue.subcategory}</div></TableCell><TableCell><Badge tone={statusTone(issue.severity)}>{label(issue.severity)}</Badge></TableCell><TableCell><Badge tone={statusTone(issue.status)}>{label(issue.status)}</Badge></TableCell><TableCell>{formatDate(issue.created_at)}</TableCell><TableCell><form action={updateIssue} style={{ display: "flex", gap: ".4rem" }}><input type="hidden" name="issue_id" value={issue.id}/><select className="select" name="status" defaultValue={issue.status} aria-label="حالة المشكلة"><option value="NEW">جديدة</option><option value="REVIEWING">مراجعة</option><option value="INVESTIGATING">تحقيق</option><option value="ACTION_REQUIRED">إجراء مطلوب</option><option value="RESOLVED">محلولة</option><option value="DISMISSED">مستبعدة</option></select><button className="button button-secondary">حفظ</button></form></TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="لا توجد مشكلات" description="ستظهر هنا المشكلات المدعومة بتحليل المراجعات الحقيقي." />}</CardContent></Card></>;
}

