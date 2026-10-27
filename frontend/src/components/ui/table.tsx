import * as React from "react";
import { cn } from "@/lib/utils";

export function Table({ className, ...props }: React.ComponentProps<"table">) {
  return <div className="table-wrap"><table className={cn("data-table", className)} {...props} /></div>;
}
export const TableHeader = (props: React.ComponentProps<"thead">) => <thead {...props} />;
export const TableBody = (props: React.ComponentProps<"tbody">) => <tbody {...props} />;
export const TableRow = (props: React.ComponentProps<"tr">) => <tr {...props} />;
export const TableHead = (props: React.ComponentProps<"th">) => <th {...props} />;
export const TableCell = (props: React.ComponentProps<"td">) => <td {...props} />;

