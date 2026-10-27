export function resolveRange(range = "30d") {
  const end = new Date();
  const start = new Date(end);
  const days = range === "today" ? 0 : range === "7d" ? 6 : range === "3m" ? 89 : 29;
  start.setUTCDate(start.getUTCDate() - days);
  const iso = (date: Date) => date.toISOString().slice(0, 10);
  return { startDate: iso(start), endDate: iso(end) };
}

