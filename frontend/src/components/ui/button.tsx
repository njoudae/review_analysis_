import * as React from "react";
import { cn } from "@/lib/utils";

export function Button({ className, variant = "primary", ...props }: React.ComponentProps<"button"> & { variant?: "primary" | "secondary" | "danger" }) {
  return <button className={cn("button", `button-${variant}`, className)} {...props} />;
}

