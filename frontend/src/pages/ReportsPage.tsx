import {
  ArrowDown,
  ArrowUp,
  Loader2,
  Minus,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  reportApi,
  transactionApi,
  type ReportResponse,
} from "@/lib/api";

function formatMonthDisplay(monthKey: string): string {
  const [year, month] = monthKey.split("-");
  const date = new Date(parseInt(year), parseInt(month) - 1);
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

function pctChange(current: number, previous: number): number | null {
  if (previous === 0) return current > 0 ? 100 : null;
  return ((current - previous) / previous) * 100;
}

export default function ReportsPage() {
  const [months, setMonths] = useState<string[]>([]);
  const [monthA, setMonthA] = useState("");
  const [monthB, setMonthB] = useState("");
  const [reportA, setReportA] = useState<ReportResponse | null>(null);
  const [reportB, setReportB] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    transactionApi.months().then((m) => {
      setMonths(m);
      if (m.length >= 2) {
        setMonthA(m[m.length - 1]);
        setMonthB(m[m.length - 2]);
      } else if (m.length === 1) {
        setMonthA(m[0]);
      }
    });
  }, []);

  useEffect(() => {
    if (!monthA) return;
    const fetchReports = async () => {
      try {
        const promises: Promise<ReportResponse>[] = [reportApi.get(monthA)];
        if (monthB) promises.push(reportApi.get(monthB));
        const results = await Promise.all(promises);
        setReportA(results[0]);
        setReportB(results[1] || null);
      } catch {
        setReportA(null);
        setReportB(null);
      }
      setLoading(false);
    };
    fetchReports();
  }, [monthA, monthB]);

  // Combine all categories from both reports
  const allCategories = new Set<string>();
  if (reportA) Object.keys(reportA.spending).forEach((c) => allCategories.add(c));
  if (reportB) Object.keys(reportB.spending).forEach((c) => allCategories.add(c));

  const comparisonData = Array.from(allCategories)
    .map((cat) => {
      const currentAmount = reportA?.spending[cat] || 0;
      const prevAmount = reportB?.spending[cat] || 0;
      const diff = currentAmount - prevAmount;
      const pct = pctChange(currentAmount, prevAmount);
      return { category: cat, current: currentAmount, previous: prevAmount, diff, pct };
    })
    .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff));

  const totalCurrent = reportA?.total_spent || 0;
  const totalPrev = reportB?.total_spent || 0;
  const totalDiff = totalCurrent - totalPrev;
  const totalPct = pctChange(totalCurrent, totalPrev);

  return (
    <div className="max-w-5xl mx-auto py-12 px-6">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-white/90 mb-1">
          Month Comparison
        </h1>
        <p className="text-white/40 text-sm">
          Compare spending side-by-side across months
        </p>
      </div>

      {/* Month Selectors */}
      <div className="flex flex-wrap gap-4 mb-8">
        <div className="flex items-center gap-2">
          <label className="text-white/40 text-xs uppercase tracking-wider">
            Current
          </label>
          <select
            value={monthA}
            onChange={(e) => setMonthA(e.target.value)}
            className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/70 text-sm focus:outline-none focus:border-amber-500/40 cursor-pointer"
          >
            {months.map((m) => (
              <option key={m} value={m}>
                {formatMonthDisplay(m)}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-white/40 text-xs uppercase tracking-wider">
            Compare to
          </label>
          <select
            value={monthB}
            onChange={(e) => setMonthB(e.target.value)}
            className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/70 text-sm focus:outline-none focus:border-amber-500/40 cursor-pointer"
          >
            <option value="">None</option>
            {months
              .filter((m) => m !== monthA)
              .map((m) => (
                <option key={m} value={m}>
                  {formatMonthDisplay(m)}
                </option>
              ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-white/20">
          <Loader2 className="w-6 h-6 animate-spin" />
        </div>
      ) : months.length === 0 ? (
        <div className="text-center py-20 rounded-xl bg-white/[0.02] border border-white/[0.06]">
          <p className="text-white/30 text-sm">No months with data yet</p>
          <p className="text-white/15 text-xs mt-1">Upload transactions to get started</p>
        </div>
      ) : (
        <>
          {/* Totals Summary */}
          <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-8">
            <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
              <p className="text-white/35 text-xs uppercase tracking-wider mb-1">
                {monthA ? formatMonthDisplay(monthA) : "Current"}
              </p>
              <p className="text-2xl font-bold text-white/90 tabular-nums">
                ${totalCurrent.toFixed(2)}
              </p>
            </div>
            {reportB && (
              <>
                <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <p className="text-white/35 text-xs uppercase tracking-wider mb-1">
                    {formatMonthDisplay(monthB)}
                  </p>
                  <p className="text-2xl font-bold text-white/90 tabular-nums">
                    ${totalPrev.toFixed(2)}
                  </p>
                </div>
                <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                  <p className="text-white/35 text-xs uppercase tracking-wider mb-1">
                    Difference
                  </p>
                  <div className="flex items-center gap-2">
                    <p
                      className={`text-2xl font-bold tabular-nums ${
                        totalDiff > 0 ? "text-red-400" : totalDiff < 0 ? "text-emerald-400" : "text-white/50"
                      }`}
                    >
                      {totalDiff > 0 ? "+" : ""}${totalDiff.toFixed(2)}
                    </p>
                    {totalPct !== null && (
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          totalDiff > 0
                            ? "bg-red-500/15 text-red-400"
                            : "bg-emerald-500/15 text-emerald-400"
                        }`}
                      >
                        {totalPct > 0 ? "+" : ""}
                        {totalPct.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Category Comparison Table */}
          <div className="rounded-xl border border-white/[0.06] overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                    Category
                  </th>
                  <th className="text-right text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                    {monthA ? formatMonthDisplay(monthA) : "Current"}
                  </th>
                  {reportB && (
                    <>
                      <th className="text-right text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                        {formatMonthDisplay(monthB)}
                      </th>
                      <th className="text-right text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                        Change
                      </th>
                      <th className="text-right text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                        %
                      </th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {comparisonData.map(({ category, current, previous, diff, pct }) => (
                  <tr
                    key={category}
                    className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3 text-sm text-white/70">
                      {category}
                    </td>
                    <td className="px-4 py-3 text-sm text-white/70 text-right tabular-nums font-medium">
                      ${current.toFixed(2)}
                    </td>
                    {reportB && (
                      <>
                        <td className="px-4 py-3 text-sm text-white/40 text-right tabular-nums">
                          ${previous.toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span
                            className={`inline-flex items-center gap-1 text-sm tabular-nums font-medium ${
                              diff > 0
                                ? "text-red-400"
                                : diff < 0
                                  ? "text-emerald-400"
                                  : "text-white/25"
                            }`}
                          >
                            {diff > 0 ? (
                              <ArrowUp className="w-3 h-3" />
                            ) : diff < 0 ? (
                              <ArrowDown className="w-3 h-3" />
                            ) : (
                              <Minus className="w-3 h-3" />
                            )}
                            ${Math.abs(diff).toFixed(2)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {pct !== null ? (
                            <span
                              className={`text-xs px-1.5 py-0.5 rounded ${
                                diff > 0
                                  ? "bg-red-500/15 text-red-400"
                                  : diff < 0
                                    ? "bg-emerald-500/15 text-emerald-400"
                                    : "bg-white/5 text-white/25"
                              }`}
                            >
                              {pct > 0 ? "+" : ""}
                              {pct.toFixed(1)}%
                            </span>
                          ) : (
                            <span className="text-white/15 text-xs">new</span>
                          )}
                        </td>
                      </>
                    )}
                  </tr>
                ))}
                {comparisonData.length === 0 && (
                  <tr>
                    <td
                      colSpan={reportB ? 5 : 2}
                      className="px-4 py-12 text-center text-white/20 text-sm"
                    >
                      No spending data available
                    </td>
                  </tr>
                )}
              </tbody>
              {reportB && comparisonData.length > 0 && (
                <tfoot>
                  <tr className="border-t border-white/[0.08]">
                    <td className="px-4 py-3 text-sm text-white/70 font-semibold">
                      Total
                    </td>
                    <td className="px-4 py-3 text-sm text-white/90 text-right tabular-nums font-bold">
                      ${totalCurrent.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-white/50 text-right tabular-nums font-medium">
                      ${totalPrev.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={`text-sm tabular-nums font-bold ${
                          totalDiff > 0 ? "text-red-400" : "text-emerald-400"
                        }`}
                      >
                        {totalDiff > 0 ? "+" : ""}${totalDiff.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {totalPct !== null && (
                        <span
                          className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                            totalDiff > 0
                              ? "bg-red-500/15 text-red-400"
                              : "bg-emerald-500/15 text-emerald-400"
                          }`}
                        >
                          {totalPct > 0 ? "+" : ""}
                          {totalPct.toFixed(1)}%
                        </span>
                      )}
                    </td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </>
      )}
    </div>
  );
}
