import { useState, type FormEvent } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login, user, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (loading) return null;
  if (user) return <Navigate to="/chat" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email || !password) {
      setError("Please fill in all fields");
      return;
    }
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] flex">
      {/* Left decorative panel */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden items-center justify-center">
        {/* Layered gradient backdrop */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#0f0f10] via-[#141416] to-[#0a0a0b]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_50%,rgba(196,164,116,0.08),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_80%_20%,rgba(196,164,116,0.04),transparent_50%)]" />

        {/* Geometric accent lines */}
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-[20%] left-[10%] w-[1px] h-[200px] bg-gradient-to-b from-transparent via-amber-500/20 to-transparent" />
          <div className="absolute top-[40%] right-[20%] w-[1px] h-[300px] bg-gradient-to-b from-transparent via-amber-500/10 to-transparent" />
          <div className="absolute bottom-[15%] left-[30%] w-[200px] h-[1px] bg-gradient-to-r from-transparent via-amber-500/15 to-transparent" />
          <div className="absolute top-[25%] left-[15%] w-[120px] h-[1px] bg-gradient-to-r from-amber-500/20 to-transparent" />
        </div>

        {/* Floating geometric shapes */}
        <div className="absolute top-[15%] right-[25%] w-24 h-24 border border-amber-500/10 rotate-45 rounded-sm" />
        <div className="absolute bottom-[20%] left-[20%] w-16 h-16 border border-amber-500/[0.07] rotate-12 rounded-sm" />
        <div className="absolute top-[60%] right-[15%] w-8 h-8 bg-amber-500/[0.06] rotate-45 rounded-sm" />

        {/* Content */}
        <div className="relative z-10 px-16 max-w-xl">
          <div className="mb-10">
            <div className="flex items-center gap-3 mb-8">
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
          </div>

          <h1 className="font-serif text-5xl leading-[1.15] text-white/95 mb-6 tracking-tight">
            Your money,
            <br />
            <span className="text-amber-400/90">clarified.</span>
          </h1>
          <p className="text-white/40 text-lg leading-relaxed max-w-sm">
            AI-powered insights that turn your spending into a clear path
            forward. No judgment — just clarity.
          </p>

          {/* Decorative divider */}
          <div className="mt-12 flex items-center gap-4">
            <div className="w-12 h-[1px] bg-amber-500/30" />
            <div className="w-1.5 h-1.5 rounded-full bg-amber-500/40" />
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 sm:px-12">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-12">
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

          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-white/95 mb-2">
              Welcome back
            </h2>
            <p className="text-white/40 text-sm">
              Sign in to continue to your dashboard
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/90 placeholder:text-white/20 focus:outline-none focus:border-amber-500/40 focus:bg-white/[0.06] transition-all duration-200 text-sm"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-white/50 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/90 placeholder:text-white/20 focus:outline-none focus:border-amber-500/40 focus:bg-white/[0.06] transition-all duration-200 text-sm"
                placeholder="Enter your password"
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 mt-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#0a0a0b] font-semibold text-sm rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-amber-500/10 hover:shadow-amber-500/20 cursor-pointer"
            >
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-[#0a0a0b]/30 border-t-[#0a0a0b] rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-white/30">
            Don&apos;t have an account?{" "}
            <Link
              to="/register"
              className="text-amber-400/80 hover:text-amber-400 transition-colors"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
