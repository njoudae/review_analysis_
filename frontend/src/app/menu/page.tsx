import { createMenuCategory, createMenuItem } from "@/app/actions";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { backendFetch, getOrganization } from "@/lib/api";

type Category = { id: string; name: string };
type Item = { id: string; category_id: string; name: string; description?: string; status: string };

export default async function MenuPage() {
  const organization = await getOrganization();
  if (!organization) return <EmptyState title="لا توجد مؤسسة" description="أضف المؤسسة أولًا." href="/settings" action="إعداد المؤسسة" />;
  if (!["restaurant", "cafe"].includes(organization.business_type)) return <><PageHeader title="القائمة" /><EmptyState title="إدارة القائمة غير متاحة" description="هذه الوحدة متاحة فقط عندما يكون نوع النشاط مطعمًا أو مقهى." /></>;
  const [categories, items] = await Promise.all([backendFetch<Category[]>(`/menu/categories?organization_id=${organization.id}`), backendFetch<Item[]>(`/menu/items?organization_id=${organization.id}`)]);
  const categoryMap = new Map(categories.map((category) => [category.id, category.name]));
  return <><PageHeader title="القائمة" description="المنتجات التي يستخدمها النظام لمطابقة الإشارات في المراجعات" /><div className="split-grid"><div className="stack"><Card><CardHeader><CardTitle>فئة جديدة</CardTitle></CardHeader><CardContent><form action={createMenuCategory} className="form-grid"><input type="hidden" name="organization_id" value={organization.id}/><div className="field full"><label htmlFor="category_name">اسم الفئة</label><input className="input" id="category_name" name="name" required /></div><div className="form-actions"><button className="button button-primary">إضافة الفئة</button></div></form></CardContent></Card><Card><CardHeader><CardTitle>منتج جديد</CardTitle></CardHeader><CardContent>{categories.length ? <form action={createMenuItem} className="form-grid"><div className="field full"><label htmlFor="category_id">الفئة</label><select className="select" id="category_id" name="category_id" required>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></div><div className="field full"><label htmlFor="item_name">اسم المنتج</label><input className="input" id="item_name" name="name" required /></div><div className="field full"><label htmlFor="description">الوصف</label><textarea className="textarea" id="description" name="description" /></div><div className="form-actions"><button className="button button-primary">إضافة المنتج</button></div></form> : <p className="cell-muted">أضف فئة قبل إضافة المنتجات.</p>}</CardContent></Card></div><Card><CardHeader><CardTitle>المنتجات</CardTitle><Badge tone="info">{items.length}</Badge></CardHeader><CardContent>{items.length ? <Table><TableHeader><TableRow><TableHead>المنتج</TableHead><TableHead>الفئة</TableHead><TableHead>الوصف</TableHead></TableRow></TableHeader><TableBody>{items.map((item) => <TableRow key={item.id}><TableCell className="cell-title">{item.name}</TableCell><TableCell>{categoryMap.get(item.category_id) ?? "—"}</TableCell><TableCell>{item.description ?? "—"}</TableCell></TableRow>)}</TableBody></Table> : <EmptyState title="لا توجد منتجات" description="أضف المنتجات بأسمائها الحقيقية لتحسين مطابقة المراجعات." />}</CardContent></Card></div></>;
}

