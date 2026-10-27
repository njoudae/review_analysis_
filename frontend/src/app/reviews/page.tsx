import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch, getOrganization } from "@/lib/api";
import { label } from "@/lib/labels";
import type { Branch, ReviewPage } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default async function ReviewsPage({ searchParams }: { searchParams: Promise<{ search?: string; branch?: string; sentiment?: string; rating?: string; page?: string }> }) {
  const params = await searchParams;
  const organization = await getOrganization();
  if (!organization) return <EmptyState title="لا توجد مؤسسة" description="أضف المؤسسة لعرض المراجعات." href="/settings" action="إعداد المؤسسة" />;
  const page = Math.max(Number(params.page ?? 1), 1);
  const query = new URLSearchParams({ organization_id: organization.id, page: String(page), page_size: "25" });
  if (params.search) query.set("search", params.search); if (params.branch) query.set("branch_id", params.branch); if (params.sentiment) query.set("sentiment", params.sentiment); if (params.rating) query.set("rating", params.rating);
  const [reviews, branches] = await Promise.all([backendFetch<ReviewPage>(`/reviews?${query}`), backendFetch<Branch[]>(`/branches?organization_id=${organization.id}`)]);
  const branchMap = new Map(branches.map((branch) => [branch.id, branch.name]));
  return <><PageHeader title="المراجعات" description="سجل المراجعات الأصلي ونتائج التحليل" /><form className="filter-bar" method="get"><div className="field grow"><label htmlFor="search">بحث</label><input className="input" id="search" name="search" defaultValue={params.search} placeholder="نص المراجعة أو اسم المراجع" /></div><div className="field"><label htmlFor="branch">الفرع</label><select className="select" id="branch" name="branch" defaultValue={params.branch ?? ""}><option value="">الكل</option>{branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></div><div className="field"><label htmlFor="sentiment">المشاعر</label><select className="select" id="sentiment" name="sentiment" defaultValue={params.sentiment ?? ""}><option value="">الكل</option><option value="positive">إيجابية</option><option value="neutral">محايدة</option><option value="negative">سلبية</option><option value="mixed">مختلطة</option></select></div><div className="field" style={{ alignSelf: "end" }}><button className="button button-secondary">تطبيق</button></div></form><Card><CardContent>{reviews.items.length ? <Table><TableHeader><TableRow><TableHead>التقييم</TableHead><TableHead>الفرع</TableHead><TableHead>المراجع</TableHead><TableHead>المراجعة</TableHead><TableHead>التصنيف</TableHead><TableHead>الخطورة</TableHead><TableHead>التاريخ</TableHead></TableRow></TableHeader><TableBody>{reviews.items.map((review) => <TableRow key={review.id}><TableCell>{review.rating ?? "—"} ⭐</TableCell><TableCell>{branchMap.get(review.branch_id) ?? "—"}</TableCell><TableCell>{review.reviewer_name ?? "غير متاح"}</TableCell><TableCell><div className="review-excerpt" title={review.review_text}>{review.review_text || "دون نص"}</div>{review.analysis?.summary ? <div className="cell-muted">{review.analysis.summary}</div> : null}</TableCell><TableCell><Badge tone={review.analysis?.sentiment === "negative" ? "danger" : review.analysis?.sentiment === "positive" ? "success" : "neutral"}>{label(review.analysis?.sentiment)}</Badge></TableCell><TableCell><Badge tone={["critical","high"].includes(review.analysis?.severity ?? "") ? "danger" : "neutral"}>{label(review.analysis?.severity)}</Badge></TableCell><TableCell>{formatDate(review.published_at)}</TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="لا توجد مراجعات" description="شغّل أول عملية جمع بعد إضافة روابط الفروع." href="/run-history" action="سجل التشغيل" />}</CardContent></Card></>;
}

