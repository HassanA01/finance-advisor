import {
  ArrowDown,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  Lightbulb,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { useAuth } from "@/hooks/useAuth";
import {
  profileApi,
  reportApi,
  transactionApi,
  type CategorySpending,
  type ProfileResponse,
  type ReportResponse,
  type TransactionResponse,
} from "@/lib/api";

const CHART_COLORS = [
  "#f59e0b", // amber-500
  "#ef4444", // red-500
  "#22c55e", // green-500
  "#3b82f6", // blue-500
  "#a855f7", // purple-500
  "#ec4899", // pink-500
  "#06b6d4", // cyan-500
  "#f97316", // orange-500
  "#14b8a6", // teal-500
  "#8b5cf6", // violet-500
  "#64748b", // slate-500
];

function getCurrentMonthKey(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function formatMonthDisplay(monthKey: string): string {
  const [year, month] = monthKey.split("-");
  const date = new Date(parseInt(year), parseInt(month) - 1);
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

function shiftMonth(monthKey: string, delta: number): string {
  const [year, month] = monthKey.split("-").map(Number);
  const d = new Date(year, month - 1 + delta);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; payload: { fill: string } }>;
}

function ChartTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  return (
    <div className="px-3 py-2 rounded-lg bg-[#1a1a1c] border border-white/10 shadow-xl">
      <div className="flex items-center gap-2">
        <div
          className="w-2.5 h-2.5 rounded-full"
          style={{ background: item.payload.fill }}
        />
        <span className="text-white/70 text-xs">{item.name}</span>
      </div>
      <p className="text-white/90 text-sm font-semibold mt-0.5">
        ${item.value.toFixed(2)}
      </p>
    </div>
  );
}

function BudgetBar({
  category,
}: {
  category: CategorySpending;
}) {
  if (category.target === null) return null;
  const pct = Math.min((category.amount / category.target) * 100, 100);
  const overBudget = category.vs_target !== null && category.vs_target > 0;
  const overPct =
    overBudget && category.target > 0
      ? Math.min(
          ((category.amount - category.target) / category.target) * 100,
          50
        )
      : 0;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-white/60">{category.category}</span>
        <span className={overBudget ? "text-red-400" : "text-emerald-400"}>
          ${category.amount.toFixed(0)}
          <span className="text-white/25"> / ${category.target.toFixed(0)}</span>
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div className="h-full flex">
          <div
            className={`h-full rounded-full transition-all duration-700 ${
              overBudget
                ? "bg-gradient-to-r from-amber-500 to-red-500"
                : "bg-gradient-to-r from-amber-500/70 to-amber-400"
            }`}
            style={{ width: `${pct}%` }}
          />
          {overBudget && overPct > 0 && (
            <div
              className="h-full bg-red-500/60 rounded-r-full"
              style={{ width: `${overPct}%` }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-white/[0.04] ${className || ""}`}
    />
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [months, setMonths] = useState<string[]>([]);
  const [selectedMonth, setSelectedMonth] = useState(getCurrentMonthKey());
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [recentTxns, setRecentTxns] = useState<TransactionResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    transactionApi.months().then((m) => {
      setMonths(m);
      if (m.length > 0 && !m.includes(selectedMonth)) {
        setSelectedMonth(m[m.length - 1]);
      }
    });
    profileApi.get().then(setProfile).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const [r, txns] = await Promise.all([
          reportApi.get(selectedMonth),
          transactionApi.list({ month: selectedMonth }),
        ]);
        setReport(r);
        setRecentTxns(txns.slice(0, 10));
      } catch {
        setReport(null);
        setRecentTxns([]);
      }
      setLoading(false);
    };
    fetchReport();
  }, [selectedMonth]);

  const canGoPrev = months.length > 0 && selectedMonth > months[0];
  const canGoNext =
    months.length > 0 && selectedMonth < months[months.length - 1];

  const chartData = report
    ? Object.entries(report.spending)
        .map(([name, value], i) => ({
          name,
          value,
          fill: CHART_COLORS[i % CHART_COLORS.length],
        }))
        .sort((a, b) => b.value - a.value)
    : [];

  const budgetCategories = (report?.categories || []).filter(
    (c) => c.target !== null
  );

  const incomeSpendRatio =
    profile?.net_monthly_income && report
      ? (report.total_spent / profile.net_monthly_income) * 100
      : null;

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-12 px-6">
        <div className="flex items-center justify-between mb-8">
          <SkeletonBlock className="w-48 h-8" />
          <SkeletonBlock className="w-32 h-8" />
        </div>
        <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-8">
          <SkeletonBlock className="h-24" />
          <SkeletonBlock className="h-24" />
          <SkeletonBlock className="h-24" />
        </div>
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          <SkeletonBlock className="h-72" />
          <SkeletonBlock className="h-72" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-12 px-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white/90 mb-1">
            Dashboard
          </h1>
          <p className="text-white/35 text-sm">
            Welcome back, {user?.email?.split("@")[0]}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => canGoPrev && setSelectedMonth(shiftMonth(selectedMonth, -1))}
            disabled={!canGoPrev}
            className="p-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.04] transition-colors disabled:opacity-20 disabled:cursor-not-allowed cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="text-white/70 text-sm font-medium min-w-[140px] text-center">
            {formatMonthDisplay(selectedMonth)}
          </span>
          <button
            onClick={() => canGoNext && setSelectedMonth(shiftMonth(selectedMonth, 1))}
            disabled={!canGoNext}
            className="p-2 rounded-lg text-white/30 hover:text-white/60 hover:bg-white/[0.04] transition-colors disabled:opacity-20 disabled:cursor-not-allowed cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-3 mb-8">
        <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-white/35 text-xs uppercase tracking-wider mb-2">
            Total Spent
          </p>
          <p className="text-2xl font-bold text-white/90 tabular-nums">
            ${report?.total_spent.toFixed(2) || "0.00"}
          </p>
          {incomeSpendRatio !== null && (
            <p className="text-white/30 text-xs mt-1">
              {incomeSpendRatio.toFixed(1)}% of income
            </p>
          )}
        </div>
        <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-white/35 text-xs uppercase tracking-wider mb-2">
            Budget Target
          </p>
          <p className="text-2xl font-bold text-white/90 tabular-nums">
            ${report?.total_target?.toFixed(2) || "—"}
          </p>
          {report?.total_target && report.total_spent > 0 && (
            <p
              className={`text-xs mt-1 ${
                report.total_spent > report.total_target
                  ? "text-red-400"
                  : "text-emerald-400"
              }`}
            >
              {report.total_spent > report.total_target ? (
                <span className="inline-flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />$
                  {(report.total_spent - report.total_target).toFixed(2)} over
                </span>
              ) : (
                <span className="inline-flex items-center gap-1">
                  <TrendingDown className="w-3 h-3" />$
                  {(report.total_target - report.total_spent).toFixed(2)} under
                </span>
              )}
            </p>
          )}
        </div>
        <div className="p-5 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-white/35 text-xs uppercase tracking-wider mb-2">
            Categories
          </p>
          <p className="text-2xl font-bold text-white/90 tabular-nums">
            {chartData.length}
          </p>
          <p className="text-white/30 text-xs mt-1">
            {recentTxns.length > 0
              ? `${report?.categories.length || 0} tracked`
              : "No data yet"}
          </p>
        </div>
      </div>

      {/* Main Content */}
      {chartData.length === 0 ? (
        <div className="text-center py-20 rounded-xl bg-white/[0.02] border border-white/[0.06]">
          <p className="text-white/30 text-sm mb-2">No spending data for this month</p>
          <Link
            to="/upload"
            className="text-amber-400 text-sm hover:text-amber-300 transition-colors"
          >
            Upload transactions to get started
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
          {/* Spending Breakdown Chart */}
          <div className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-white/70 text-sm font-medium mb-4">
              Spending Breakdown
            </h2>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {chartData.map((entry, i) => (
                      <Cell key={entry.name} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5">
              {chartData.slice(0, 6).map((item) => (
                <div key={item.name} className="flex items-center gap-1.5">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ background: item.fill }}
                  />
                  <span className="text-white/40 text-xs">{item.name}</span>
                </div>
              ))}
              {chartData.length > 6 && (
                <span className="text-white/20 text-xs">
                  +{chartData.length - 6} more
                </span>
              )}
            </div>
          </div>

          {/* Budget Progress */}
          <div className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <h2 className="text-white/70 text-sm font-medium mb-4">
              Budget Progress
            </h2>
            {budgetCategories.length > 0 ? (
              <div className="space-y-4">
                {budgetCategories
                  .sort(
                    (a, b) =>
                      (b.vs_target ?? 0) - (a.vs_target ?? 0)
                  )
                  .map((cat) => (
                    <BudgetBar key={cat.category} category={cat} />
                  ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-white/25 text-sm">No budget targets set</p>
                <p className="text-white/15 text-xs mt-1">
                  Set targets during onboarding
                </p>
              </div>
            )}
          </div>

          {/* AI Insights */}
          {report?.summary && (
            <div className="p-6 rounded-xl bg-gradient-to-br from-amber-500/[0.06] to-transparent border border-amber-500/10">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h2 className="text-amber-400/80 text-sm font-medium">
                  AI Insights
                </h2>
              </div>
              <p className="text-white/60 text-sm leading-relaxed mb-4">
                {report.summary}
              </p>
              {report.insights && report.insights.length > 0 && (
                <ul className="space-y-2">
                  {report.insights.map((insight, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Lightbulb className="w-3.5 h-3.5 text-amber-400/50 mt-0.5 shrink-0" />
                      <span className="text-white/50 text-xs leading-relaxed">
                        {insight}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Recent Transactions */}
          <div className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white/70 text-sm font-medium">
                Recent Transactions
              </h2>
              <Link
                to={`/transactions?month=${selectedMonth}`}
                className="text-amber-400/60 text-xs hover:text-amber-400 transition-colors"
              >
                View all
              </Link>
            </div>
            {recentTxns.length > 0 ? (
              <div className="space-y-2">
                {recentTxns.map((txn) => (
                  <div
                    key={txn.id}
                    className="flex items-center justify-between py-2 border-b border-white/[0.03] last:border-0"
                  >
                    <div className="min-w-0">
                      <p className="text-white/60 text-sm truncate">
                        {txn.description}
                      </p>
                      <p className="text-white/20 text-xs">{txn.category}</p>
                    </div>
                    <span className="text-white/70 text-sm tabular-nums font-medium ml-4 shrink-0">
                      ${txn.amount.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/20 text-sm text-center py-8">
                No transactions
              </p>
            )}
          </div>

          {/* Month-over-Month Quick View */}
          {report && Object.keys(report.vs_prev_month).length > 0 && (
            <div className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06] lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-white/70 text-sm font-medium">
                  vs. Previous Month
                </h2>
                <Link
                  to="/reports"
                  className="text-amber-400/60 text-xs hover:text-amber-400 transition-colors"
                >
                  Full comparison
                </Link>
              </div>
              <div className="grid gap-3 grid-cols-2 md:grid-cols-4">
                {Object.entries(report.vs_prev_month)
                  .filter(([, v]) => v.current > 0 || v.previous > 0)
                  .sort(([, a], [, b]) => Math.abs(b.diff) - Math.abs(a.diff))
                  .slice(0, 8)
                  .map(([cat, data]) => (
                    <div
                      key={cat}
                      className="px-3 py-2.5 rounded-lg bg-white/[0.02]"
                    >
                      <p className="text-white/40 text-xs truncate mb-1">
                        {cat}
                      </p>
                      <div className="flex items-center gap-1.5">
                        {data.diff > 0 ? (
                          <ArrowUp className="w-3 h-3 text-red-400" />
                        ) : data.diff < 0 ? (
                          <ArrowDown className="w-3 h-3 text-emerald-400" />
                        ) : null}
                        <span
                          className={`text-sm font-medium tabular-nums ${
                            data.diff > 0
                              ? "text-red-400"
                              : data.diff < 0
                                ? "text-emerald-400"
                                : "text-white/40"
                          }`}
                        >
                          {data.diff > 0 ? "+" : ""}${data.diff.toFixed(0)}
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
