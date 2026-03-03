import {
  ArrowRight,
  Bot,
  CheckCircle2,
  Loader2,
  Send,
  SkipForward,
  User,
} from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import {
  onboardingApi,
  profileApi,
  type ProfileResponse,
} from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const STEPS = [
  "Income",
  "Fixed Expenses",
  "Debts",
  "Budget Targets",
  "Family Support",
  "Emergency Fund",
  "Risk Tolerance",
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [complete, setComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    profileApi.get().then(setProfile);
  }, []);

  // Start conversation automatically
  useEffect(() => {
    if (messages.length === 0 && !loading) {
      sendMessage("Hi! I'm ready to set up my financial profile.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    const userMsg: ChatMessage = { role: "user", content: text };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const history = newMessages.slice(0, -1).map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const res = await onboardingApi.chat(text, history);

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply },
      ]);

      if (res.profile_update) {
        setCurrentStep((s) => Math.min(s + 1, STEPS.length - 1));
        // Refresh profile
        const updated = await profileApi.get();
        setProfile(updated);
      }

      if (res.onboarding_complete) {
        setComplete(true);
        setCurrentStep(STEPS.length);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I'm having trouble connecting right now. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
  };

  const handleSkip = () => {
    if (loading) return;
    sendMessage("Skip this section");
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] flex">
      {/* Sidebar — step progress + profile summary */}
      <div className="hidden lg:flex lg:w-80 flex-col border-r border-white/[0.06] bg-white/[0.01]">
        <div className="p-6 border-b border-white/[0.06]">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-7 h-7 rounded-md bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
              <svg
                className="w-3.5 h-3.5 text-[#0a0a0b]"
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
            <span className="text-white/80 text-sm font-medium">
              Profile Setup
            </span>
          </div>
        </div>

        {/* Steps */}
        <div className="p-6 space-y-1">
          {STEPS.map((step, i) => (
            <div
              key={step}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                i < currentStep
                  ? "text-amber-400/80"
                  : i === currentStep
                    ? "text-white/90 bg-white/[0.04]"
                    : "text-white/25"
              }`}
            >
              {i < currentStep ? (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              ) : (
                <div
                  className={`w-4 h-4 rounded-full border shrink-0 ${
                    i === currentStep
                      ? "border-amber-500/60"
                      : "border-white/15"
                  }`}
                />
              )}
              {step}
            </div>
          ))}
        </div>

        {/* Profile summary */}
        {profile && (profile.net_monthly_income || profile.pay_frequency) && (
          <div className="mt-auto p-6 border-t border-white/[0.06]">
            <p className="text-xs text-white/30 uppercase tracking-wider mb-3">
              Your Profile
            </p>
            <div className="space-y-2 text-sm">
              {profile.net_monthly_income && (
                <div className="flex justify-between">
                  <span className="text-white/40">Income</span>
                  <span className="text-white/70">
                    ${profile.net_monthly_income.toLocaleString()}
                  </span>
                </div>
              )}
              {profile.pay_frequency && (
                <div className="flex justify-between">
                  <span className="text-white/40">Pay</span>
                  <span className="text-white/70 capitalize">
                    {profile.pay_frequency}
                  </span>
                </div>
              )}
              {Object.keys(profile.budget_targets).length > 0 && (
                <div className="flex justify-between">
                  <span className="text-white/40">Budgets</span>
                  <span className="text-white/70">
                    {Object.keys(profile.budget_targets).length} categories
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/[0.06] flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-white/90">
              Financial Profile Setup
            </h1>
            <p className="text-sm text-white/35">
              Chat with your advisor to configure your profile
            </p>
          </div>
          {!complete && (
            <button
              onClick={handleSkip}
              disabled={loading}
              className="flex items-center gap-1.5 text-xs text-white/30 hover:text-white/60 transition-colors disabled:opacity-50 cursor-pointer"
            >
              <SkipForward className="w-3.5 h-3.5" />
              Skip section
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages
            .filter((m) => !(m.role === "user" && messages.indexOf(m) === 0))
            .map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
              >
                {msg.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                )}
                <div
                  className={`max-w-lg rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-amber-500/10 text-white/80 rounded-br-md"
                      : "bg-white/[0.04] text-white/70 rounded-bl-md"
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === "user" && (
                  <div className="w-7 h-7 rounded-full bg-white/[0.06] border border-white/[0.1] flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5 text-white/50" />
                  </div>
                )}
              </div>
            ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
                <Bot className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="bg-white/[0.04] rounded-2xl rounded-bl-md px-4 py-3">
                <Loader2 className="w-4 h-4 text-white/30 animate-spin" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {complete ? (
          <div className="px-6 py-6 border-t border-white/[0.06]">
            <button
              onClick={() => navigate("/dashboard")}
              className="w-full py-3 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-[#0a0a0b] font-semibold text-sm rounded-lg transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              Go to Dashboard
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="px-6 py-4 border-t border-white/[0.06]"
          >
            <div className="flex gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your response..."
                disabled={loading}
                className="flex-1 px-4 py-3 bg-white/[0.04] border border-white/[0.08] rounded-lg text-white/90 placeholder:text-white/20 focus:outline-none focus:border-amber-500/40 transition-all text-sm disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-4 py-3 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 rounded-lg text-amber-400 transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
