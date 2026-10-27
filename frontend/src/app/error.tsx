"use client";

import { Button } from "@/components/ui/button";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <div className="error-state"><h2>تعذر تحميل البيانات</h2><p>تأكد من تشغيل الخادم الخلفي وصحة متغيرات البيئة، ثم أعد المحاولة.</p><Button onClick={reset}>إعادة المحاولة</Button></div>;
}

