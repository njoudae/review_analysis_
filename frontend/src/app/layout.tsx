import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/sidebar";

export const metadata: Metadata = { title: "بصيرة | ذكاء تجربة العملاء", description: "لوحة إدارة وتحليل مراجعات العملاء" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ar" dir="rtl" className="dark"><body><div className="app-shell"><Sidebar /><main className="main-content">{children}</main></div></body></html>;
}

