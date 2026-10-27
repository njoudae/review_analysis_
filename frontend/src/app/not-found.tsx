import Link from "next/link";

export default function NotFound() {
  return <div className="error-state"><h2>الصفحة غير موجودة</h2><Link className="button button-primary" href="/">العودة للوحة القيادة</Link></div>;
}

