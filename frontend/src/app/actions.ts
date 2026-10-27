"use server";

import { revalidatePath } from "next/cache";
import { backendFetch } from "@/lib/api";

function value(form: FormData, key: string) {
  const item = form.get(key);
  return typeof item === "string" && item.trim() ? item.trim() : undefined;
}

export async function createOrganization(form: FormData) {
  await backendFetch("/organizations", {
    method: "POST",
    body: JSON.stringify({
      name: value(form, "name"),
      business_type: value(form, "business_type"),
      industry: value(form, "industry"),
      city: value(form, "city"),
      default_language: "ar",
      timezone: value(form, "timezone") ?? "Asia/Riyadh",
    }),
  });
  revalidatePath("/");
  revalidatePath("/settings");
}

export async function createBranch(form: FormData) {
  await backendFetch("/branches", {
    method: "POST",
    body: JSON.stringify({
      organization_id: value(form, "organization_id"),
      name: value(form, "name"),
      city: value(form, "city"),
      district: value(form, "district"),
      address: value(form, "address"),
      google_maps_url: value(form, "google_maps_url"),
      manager_name: value(form, "manager_name"),
      phone: value(form, "phone"),
      status: "active",
    }),
  });
  revalidatePath("/branches");
}

export async function createEmployee(form: FormData) {
  await backendFetch("/employees", {
    method: "POST",
    body: JSON.stringify({
      organization_id: value(form, "organization_id"),
      branch_id: value(form, "branch_id"),
      employee_code: value(form, "employee_code"),
      first_name: value(form, "first_name"),
      last_name: value(form, "last_name"),
      gender: value(form, "gender"),
      nationality: value(form, "nationality"),
      job_title: value(form, "job_title"),
      joined_at: value(form, "joined_at"),
      status: "active",
    }),
  });
  revalidatePath("/employees");
  revalidatePath("/branches");
}

export async function createMenuCategory(form: FormData) {
  await backendFetch("/menu/categories", {
    method: "POST",
    body: JSON.stringify({ organization_id: value(form, "organization_id"), name: value(form, "name") }),
  });
  revalidatePath("/menu");
}

export async function createMenuItem(form: FormData) {
  await backendFetch("/menu/items", {
    method: "POST",
    body: JSON.stringify({
      category_id: value(form, "category_id"),
      name: value(form, "name"),
      description: value(form, "description"),
      status: "active",
    }),
  });
  revalidatePath("/menu");
}

export async function enqueueRun(form: FormData) {
  await backendFetch("/runs", {
    method: "POST",
    body: JSON.stringify({ organization_id: value(form, "organization_id") }),
  });
  revalidatePath("/run-history");
}

export async function updateIssue(form: FormData) {
  const issueId = value(form, "issue_id");
  await backendFetch(`/issues/${issueId}`, {
    method: "PATCH",
    body: JSON.stringify({
      status: value(form, "status"),
      assigned_to: value(form, "assigned_to"),
      action_taken: value(form, "action_taken"),
      resolution: value(form, "resolution"),
    }),
  });
  revalidatePath("/issues");
}

