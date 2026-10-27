"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Building2, ClipboardList, History, LayoutDashboard, MenuSquare, MessageSquareText, Settings, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const groups = [
  { label: "نظرة عامة", links: [{ href: "/", label: "لوحة القيادة", icon: LayoutDashboard }] },
  { label: "المؤسسة", links: [{ href: "/branches", label: "الفروع", icon: Building2 }, { href: "/employees", label: "الموظفون", icon: Users }, { href: "/menu", label: "القائمة", icon: MenuSquare }] },
  { label: "تجربة العملاء", links: [{ href: "/reviews", label: "المراجعات", icon: MessageSquareText }, { href: "/issues", label: "المشكلات", icon: ClipboardList }] },
  { label: "التحليلات", links: [{ href: "/run-history", label: "سجل التشغيل والتقارير", icon: History }] },
  { label: "الإدارة", links: [{ href: "/settings", label: "الإعدادات", icon: Settings }] },
];

export function Sidebar() {
  const pathname = usePathname();
  return <aside className="sidebar"><div className="brand"><span className="brand-mark">CX</span><div><strong>بصيرة</strong><small>ذكاء تجربة العملاء</small></div></div><nav aria-label="التنقل الرئيسي">{groups.map((group) => <div className="nav-group" key={group.label}><p>{group.label}</p>{group.links.map(({ href, label, icon: Icon }) => { const active = href === "/" ? pathname === "/" : pathname.startsWith(href); return <Link key={`${href}-${label}`} href={href} className={cn("nav-link", active && "active")}><Icon aria-hidden="true" /><span>{label}</span></Link>; })}</div>)}</nav></aside>;
}
