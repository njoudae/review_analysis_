import { Play } from "lucide-react";
import { enqueueRun } from "@/app/actions";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch, getOrganization } from "@/lib/api";
import { label, statusTone } from "@/lib/labels";
import type { Run } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default async function RunHistoryPage() {
  const organization = await getOrganization();
  if (!organization) return <EmptyState title="لا توجد مؤسسة" description="أضف المؤسسة أولًا." href="/settings" action="إعداد المؤسسة" />;
  const runs = await backendFetch<Run[]>(`/runs?organization_id=${organization.id}`);
  return <><PageHeader title="سجل التشغيل" description="سجل قابل للتدقيق لعمليات الجمع والتحليل والتقرير" actions={<form action={enqueueRun}><input type="hidden" name="organization_id" value={organization.id}/><button className="button button-primary"><Play size={15} aria-hidden="true" />بدء عملية جمع</button></form>} /><div className="notice">إنشاء العملية يضعها في قائمة الانتظار. يجب تشغيل العامل المستقل لمعالجتها خارج دورة طلب HTTP.</div><Card className="section-space"><CardContent>{runs.length ? <Table><TableHeader><TableRow><TableHead>العملية</TableHead><TableHead>الحالة</TableHead><TableHead>بدأت</TableHead><TableHead>اكتملت</TableHead><TableHead>الفروع</TableHead><TableHead>المجموعة</TableHead><TableHead>الجديدة</TableHead><TableHead>المحللة</TableHead><TableHead>المشكلات</TableHead></TableRow></TableHeader><TableBody>{runs.map((run) => <TableRow key={run.id}><TableCell><span className="cell-title">{run.id.slice(0, 8)}</span>{run.last_error ? <div className="cell-muted" title={run.last_error}>يوجد خطأ مسجل</div> : null}</TableCell><TableCell><Badge tone={statusTone(run.status)}>{label(run.status)}</Badge></TableCell><TableCell>{formatDate(run.started_at ?? run.created_at)}</TableCell><TableCell>{formatDate(run.completed_at)}</TableCell><TableCell>{run.branches_processed}</TableCell><TableCell>{run.reviews_collected}</TableCell><TableCell>{run.new_reviews}</TableCell><TableCell>{run.analyzed_reviews}</TableCell><TableCell>{run.issues_generated}</TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="لم تُشغّل أي عملية" description="ابدأ أول عملية بعد إضافة فرع نشط ورابط Google Maps." />}</CardContent></Card></>;
}

