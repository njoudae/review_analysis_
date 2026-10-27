import Link from "next/link";
import { Database } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function EmptyState({ title, description, href, action }: { title: string; description: string; href?: string; action?: string }) {
  return <Card className="empty-state"><CardContent><Database aria-hidden="true" /><h2>{title}</h2><p>{description}</p>{href && action ? <Link className="button button-primary" href={href}>{action}</Link> : null}</CardContent></Card>;
}

