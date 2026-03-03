import {
  Bot,
  Loader2,
  Send,
  Trash2,
  User,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { chatApi, type ChatMessageResponse } from "@/lib/api";

const SUGGESTED_PROMPTS = [
  "How am I doing this month compared to my budget?",
  "Where can I cut spending without a big lifestyle change?",
  "What should I prioritize — saving or paying off debt?",
  "Give me a realistic plan to reduce my eating out spending.",
];

function MessageBubble({
  role,
  content,
}: {
  role: string;
  content: string;
}) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
          isUser
            ? "bg-white/[0.08]"
            : "bg-gradient-to-br from-amber-400 to-amber-600"
        }`}
      >
        {isUser ? (
          <User className="w-3.5 h-3.5 text-white/50" />
        ) : (
          <Bot className="w-3.5 h-3.5 text-[#0a0a0b]" />
        )}
      </div>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
          isUser
            ? "bg-white/[0.08] text-white/70 rounded-br-sm"
            : "bg-white/[0.03] border border-white/[0.06] text-white/60 rounded-bl-sm"
        }`}
      >
        {content.split("\n").map((line, i) => (
          <p key={i} className={i > 0 ? "mt-2" : ""}>
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-gradient-to-br from-amber-400 to-amber-600">
        <Bot className="w-3.5 h-3.5 text-[#0a0a0b]" />
      </div>
      <div className="px-4 py-3 rounded-xl rounded-bl-sm bg-white/[0.03] border border-white/[0.06]">
        <div className="flex gap-1.5 items-center h-5">
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400/50 animate-bounce [animation-delay:0ms]" />
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400/50 animate-bounce [animation-delay:150ms]" />
          <div className="w-1.5 h-1.5 rounded-full bg-amber-400/50 animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageResponse[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    chatApi
      .history()
      .then(setMessages)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending, scrollToBottom]);

  const handleSend = async () => {
    const msg = input.trim();
    if (!msg || sending) return;

    setInput("");
    setSending(true);

    // Optimistic add
    const tempUserMsg: ChatMessageResponse = {
      id: `temp-${crypto.randomUUID()}`,
      role: "user",
      content: msg,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const { reply } = await chatApi.send(msg);
      const assistantMsg: ChatMessageResponse = {
        id: `temp-${crypto.randomUUID()}`,
        role: "assistant",
        content: reply,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${crypto.randomUUID()}`,
          role: "assistant",
          content:
            "Sorry, I'm having trouble connecting right now. Please try again in a moment.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClear = async () => {
    await chatApi.clearHistory();
    setMessages([]);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-white/20">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
            <Bot className="w-4 h-4 text-[#0a0a0b]" />
          </div>
          <div>
            <h1 className="text-white/80 text-sm font-medium">
              Finance Advisor
            </h1>
            <p className="text-white/25 text-xs">
              AI-powered financial guidance
            </p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-white/20 hover:text-white/50 hover:bg-white/[0.04] transition-colors text-xs cursor-pointer"
          >
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400/20 to-amber-600/10 border border-amber-500/10 flex items-center justify-center mb-4">
              <Bot className="w-7 h-7 text-amber-400/60" />
            </div>
            <h2 className="text-white/60 text-sm font-medium mb-1">
              Ask your financial advisor
            </h2>
            <p className="text-white/25 text-xs text-center mb-6">
              I have access to your spending data, budget targets, and goals.
              Ask me anything about your finances.
            </p>
            <div className="grid gap-2 w-full">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => {
                    setInput(prompt);
                    inputRef.current?.focus();
                  }}
                  className="text-left px-4 py-3 rounded-lg bg-white/[0.02] border border-white/[0.06] hover:border-amber-500/20 hover:bg-white/[0.04] transition-all text-white/40 text-xs leading-relaxed cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                role={msg.role}
                content={msg.content}
              />
            ))}
            {sending && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-white/[0.06]">
        <div className="max-w-3xl mx-auto relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your finances..."
            rows={1}
            disabled={sending}
            className="w-full resize-none px-4 py-3 pr-12 bg-white/[0.04] border border-white/[0.08] rounded-xl text-white/70 text-sm placeholder:text-white/15 focus:outline-none focus:border-amber-500/30 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || sending}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg text-white/20 hover:text-amber-400 hover:bg-amber-500/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer"
          >
            {sending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
