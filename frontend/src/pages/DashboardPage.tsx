import { Link } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-5xl mx-auto py-12 px-6">
      <h1 className="text-2xl font-semibold text-white/90 mb-2">
        Welcome back
      </h1>
      <p className="text-white/40 text-sm mb-8">{user?.email}</p>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <Link
          to="/upload"
          className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-amber-500/20 transition-colors"
        >
          <p className="text-white/70 text-sm font-medium">
            Upload Transactions
          </p>
          <p className="text-white/30 text-xs mt-1">
            Import your bank CSV files
          </p>
        </Link>
        <Link
          to="/transactions"
          className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-amber-500/20 transition-colors"
        >
          <p className="text-white/70 text-sm font-medium">
            View Transactions
          </p>
          <p className="text-white/30 text-xs mt-1">
            Browse and filter your spending
          </p>
        </Link>
        <div className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <p className="text-white/70 text-sm font-medium">
            Chat with Advisor
          </p>
          <p className="text-white/30 text-xs mt-1">Coming soon</p>
        </div>
      </div>
    </div>
  );
}
