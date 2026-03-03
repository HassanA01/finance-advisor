import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white/90 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-12">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
              <svg
                className="w-4 h-4 text-[#0a0a0b]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
                />
              </svg>
            </div>
            <span className="text-amber-100/80 text-sm font-medium tracking-[0.2em] uppercase">
              Finance Advisor
            </span>
          </div>
          <button
            onClick={logout}
            className="text-sm text-white/40 hover:text-white/70 transition-colors cursor-pointer"
          >
            Sign out
          </button>
        </div>

        <h1 className="text-3xl font-semibold mb-2">
          Welcome back
        </h1>
        <p className="text-white/40 mb-8">{user?.email}</p>

        <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
          {["Upload Transactions", "View Reports", "Chat with Advisor"].map(
            (label) => (
              <div
                key={label}
                className="p-6 rounded-xl bg-white/[0.03] border border-white/[0.06] hover:border-amber-500/20 transition-colors"
              >
                <p className="text-white/60 text-sm">{label}</p>
                <p className="text-white/20 text-xs mt-1">Coming soon</p>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
}
