import Link from "next/link";
import { createBranch } from "@/app/actions";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch, getOrganization } from "@/lib/api";
import { label, statusTone } from "@/lib/labels";
import type { Branch } from "@/lib/types";

export default async function BranchesPage() {
  const organization = await getOrganization();
  if (!organization) return <EmptyState title="لا توجد مؤسسة" description="أضف المؤسسة قبل إنشاء الفروع." href="/settings" action="إعداد المؤسسة" />;
  const branches = await backendFetch<Branch[]>(`/branches?organization_id=${organization.id}`);
  return <><PageHeader title="الفروع" description="إدارة مصادر Google Maps وبيانات الفروع" /><div className="split-grid"><Card><CardHeader><CardTitle>إضافة فرع</CardTitle></CardHeader><CardContent><form action={createBranch} className="form-grid"><input type="hidden" name="organization_id" value={organization.id}/><div className="field"><label htmlFor="name">اسم الفرع</label><input className="input" id="name" name="name" required /></div><div className="field"><label htmlFor="city">المدينة</label><input className="input" id="city" name="city" required /></div><div className="field"><label htmlFor="district">الحي</label><input className="input" id="district" name="district" /></div><div className="field"><label htmlFor="manager_name">مدير الفرع</label><input className="input" id="manager_name" name="manager_name" /></div><div className="field full"><label htmlFor="google_maps_url">رابط Google Maps</label><input className="input" id="google_maps_url" name="google_maps_url" type="url" required /></div><div className="field full"><label htmlFor="address">العنوان</label><textarea className="textarea" id="address" name="address" /></div><div className="form-actions"><button className="button button-primary" type="submit">حفظ الفرع</button></div></form></CardContent></Card><Card><CardHeader><CardTitle>الفروع المسجلة</CardTitle><Badge tone="info">{branches.length}</Badge></CardHeader><CardContent>{branches.length ? <Table><TableHeader><TableRow><TableHead>الفرع</TableHead><TableHead>المدير</TableHead><TableHead>الموظفون</TableHead><TableHead>الحالة</TableHead></TableRow></TableHeader><TableBody>{branches.map((branch) => <TableRow key={branch.id}><TableCell><Link className="cell-title" href={`/branches/${branch.id}`}>{branch.name}</Link><div className="cell-muted">{branch.city} {branch.district ? `— ${branch.district}` : ""}</div></TableCell><TableCell>{branch.manager_name ?? "—"}</TableCell><TableCell>{branch.employee_count}</TableCell><TableCell><Badge tone={statusTone(branch.status)}>{label(branch.status)}</Badge></TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="لا توجد فروع" description="أضف أول فرع واربطه بعنوان Google Maps الحقيقي." />}</CardContent></Card></div></>;
}

