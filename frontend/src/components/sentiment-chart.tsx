"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function SentimentChart({ data }: { data: Array<{ date: string; positive: number; negative: number; neutral: number }> }) {
  if (!data.length) return <div className="chart-empty">لا توجد بيانات محللة ضمن الفترة المحددة.</div>;
  return <div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{ top: 12, right: 4, left: -22, bottom: 0 }}><defs><linearGradient id="positive" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#4ade80" stopOpacity={0.35}/><stop offset="95%" stopColor="#4ade80" stopOpacity={0}/></linearGradient><linearGradient id="negative" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#fb7185" stopOpacity={0.3}/><stop offset="95%" stopColor="#fb7185" stopOpacity={0}/></linearGradient></defs><CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false}/><XAxis dataKey="date" tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis allowDecimals={false} tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false}/><Tooltip contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 10 }} /><Area type="monotone" dataKey="positive" name="إيجابية" stroke="#4ade80" fill="url(#positive)" strokeWidth={2}/><Area type="monotone" dataKey="negative" name="سلبية" stroke="#fb7185" fill="url(#negative)" strokeWidth={2}/><Area type="monotone" dataKey="neutral" name="محايدة" stroke="#a1a1aa" fill="transparent" strokeWidth={2}/></AreaChart></ResponsiveContainer></div>;
}

