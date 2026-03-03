import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { transactionApi, type TransactionResponse } from "@/lib/api";

const CATEGORY_COLORS: Record<string, string> = {
  "Eating Out": "bg-orange-500/15 text-orange-400 border-orange-500/20",
  "Uber Eats": "bg-red-500/15 text-red-400 border-red-500/20",
  Groceries: "bg-green-500/15 text-green-400 border-green-500/20",
  "Transportation - Rideshare":
    "bg-blue-500/15 text-blue-400 border-blue-500/20",
  "Transportation - Gas": "bg-sky-500/15 text-sky-400 border-sky-500/20",
  "Transportation - Parking":
    "bg-cyan-500/15 text-cyan-400 border-cyan-500/20",
  "Transportation - Transit":
    "bg-teal-500/15 text-teal-400 border-teal-500/20",
  Shopping: "bg-purple-500/15 text-purple-400 border-purple-500/20",
  Entertainment: "bg-pink-500/15 text-pink-400 border-pink-500/20",
  "Family Support": "bg-amber-500/15 text-amber-400 border-amber-500/20",
  Investment: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  Other: "bg-white/10 text-white/50 border-white/15",
};

function CategoryBadge({ category }: { category: string }) {
  const colors =
    CATEGORY_COLORS[category] || CATEGORY_COLORS["Other"];
  return (
    <span
      className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium border ${colors}`}
    >
      {category}
    </span>
  );
}

export default function TransactionsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
  const [months, setMonths] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const selectedMonth = searchParams.get("month") || "";
  const selectedCategory = searchParams.get("category") || "";
  const searchTerm = searchParams.get("search") || "";

  useEffect(() => {
    transactionApi.months().then(setMonths);
    transactionApi.categories().then(setCategories);
  }, []);

  useEffect(() => {
    transactionApi
      .list({
        month: selectedMonth || undefined,
        category: selectedCategory || undefined,
        search: searchTerm || undefined,
      })
      .then(setTransactions)
      .finally(() => setLoading(false));
  }, [selectedMonth, selectedCategory, searchTerm]);

  const updateFilter = (key: string, value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) params.set(key, value);
    else params.delete(key);
    setSearchParams(params);
  };

  const totalAmount = transactions.reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="max-w-5xl mx-auto py-12 px-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-white/90 mb-1">
            Transactions
          </h1>
          <p className="text-white/40 text-sm">
            {transactions.length} transactions
            {selectedMonth && ` in ${selectedMonth}`}
            {" \u2022 "}${totalAmount.toFixed(2)} total
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={selectedMonth}
          onChange={(e) => updateFilter("month", e.target.value)}
          className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/70 text-sm focus:outline-none focus:border-amber-500/40 cursor-pointer"
        >
          <option value="">All months</option>
          {months.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <select
          value={selectedCategory}
          onChange={(e) => updateFilter("category", e.target.value)}
          className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/70 text-sm focus:outline-none focus:border-amber-500/40 cursor-pointer"
        >
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/25" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => updateFilter("search", e.target.value)}
            placeholder="Search transactions..."
            className="w-full pl-9 pr-4 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/70 text-sm placeholder:text-white/20 focus:outline-none focus:border-amber-500/40"
          />
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-center py-16 text-white/20">Loading...</div>
      ) : transactions.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-white/30 text-sm">No transactions found</p>
          <p className="text-white/15 text-xs mt-1">
            Upload a CSV to get started
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-white/[0.06] overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                  Date
                </th>
                <th className="text-left text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                  Description
                </th>
                <th className="text-left text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                  Category
                </th>
                <th className="text-right text-xs text-white/30 uppercase tracking-wider px-4 py-3 font-medium">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr
                  key={txn.id}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-white/40 tabular-nums">
                    {new Date(txn.date).toLocaleDateString("en-CA")}
                  </td>
                  <td className="px-4 py-3 text-sm text-white/70">
                    {txn.description}
                  </td>
                  <td className="px-4 py-3">
                    <CategoryBadge category={txn.category} />
                  </td>
                  <td className="px-4 py-3 text-sm text-white/70 text-right tabular-nums font-medium">
                    ${txn.amount.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
