import {
  Bot,
  FileText,
  Loader2,
  Paperclip,
  Send,
  Trash2,
  User,
  X,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { chatApi, profileApi, type ChatMessageResponse } from "@/lib/api";

const SUGGESTED_PROMPTS = [
  "Upload my bank transactions for this month",
  "Help me create a budget based on my spending",
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
        {isUser ? (
          content.split("\n").map((line, i) => (
            <p key={i} className={i > 0 ? "mt-2" : ""}>
              {line}
            </p>
          ))
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-headings:text-white/80 prose-headings:font-semibold prose-p:text-white/60 prose-strong:text-white/70 prose-li:text-white/60 prose-a:text-amber-400 prose-code:text-amber-300/80 prose-code:bg-white/[0.06] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-white/[0.04] prose-pre:border prose-pre:border-white/[0.06] prose-table:text-white/60 prose-th:text-white/70 prose-th:border-white/[0.1] prose-td:border-white/[0.06] prose-hr:border-white/[0.08]">
            <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator({ label }: { label?: string }) {
  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-gradient-to-br from-amber-400 to-amber-600">
        <Bot className="w-3.5 h-3.5 text-[#0a0a0b]" />
      </div>
      <div className="px-4 py-3 rounded-xl rounded-bl-sm bg-white/[0.03] border border-white/[0.06]">
        <div className="flex gap-2 items-center">
          <div className="flex gap-1.5 items-center h-5">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400/50 animate-bounce [animation-delay:0ms]" />
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400/50 animate-bounce [animation-delay:150ms]" />
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400/50 animate-bounce [animation-delay:300ms]" />
          </div>
          {label && (
            <span className="text-white/20 text-xs ml-1">{label}</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageResponse[]>([]);
  const [input, setInput] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sendingLabel, setSendingLabel] = useState<string>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const autoGreetSent = useRef(false);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  // Load history and check if auto-greet is needed
  useEffect(() => {
    const init = async () => {
      try {
        const history = await chatApi.history();
        setMessages(history);

        // Auto-greet: if no history and onboarding not complete, send greeting
        if (history.length === 0 && !autoGreetSent.current) {
          autoGreetSent.current = true;
          try {
            const profile = await profileApi.get();
            if (!profile.onboarding_complete) {
              setLoading(false);
              await sendMessage("Hi, I just signed up!");
              return;
            }
          } catch {
            // Profile fetch failed — proceed normally
          }
        }
      } catch {
        // History fetch failed
      } finally {
        setLoading(false);
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending, scrollToBottom]);

  const sendMessage = async (text?: string, uploadFiles?: File[]) => {
    const msg = text ?? input.trim();
    const filesToSend = uploadFiles ?? files;
    if ((!msg && filesToSend.length === 0) || sending) return;

    if (!text) setInput("");
    if (!uploadFiles) setFiles([]);
    setSending(true);
    setSendingLabel(filesToSend.length > 0 ? "Analyzing your transactions..." : undefined);

    // Optimistic add
    const displayMsg = msg || `[Uploaded ${filesToSend.length} file${filesToSend.length > 1 ? "s" : ""}]`;
    const tempUserMsg: ChatMessageResponse = {
      id: `temp-${crypto.randomUUID()}`,
      role: "user",
      content: displayMsg,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const { reply } = await chatApi.send(msg, filesToSend.length > 0 ? filesToSend : undefined);
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
      setSendingLabel(undefined);
      inputRef.current?.focus();
    }
  };

  const handleSend = () => sendMessage();

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (selected) {
      const csvFiles = Array.from(selected).filter(
        (f) => f.name.toLowerCase().endsWith(".csv")
      );
      setFiles((prev) => [...prev, ...csvFiles]);
    }
    // Reset input so the same file can be re-selected
    e.target.value = "";
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter(
      (f) => f.name.toLowerCase().endsWith(".csv")
    );
    setFiles((prev) => [...prev, ...dropped]);
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
    <div
      className="flex flex-col h-full"
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
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
              Your personal financial advisor
            </h2>
            <p className="text-white/25 text-xs text-center mb-6">
              Upload your bank statements, get personalized budgets, and track
              your progress — all through conversation.
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
            {sending && <TypingIndicator label={sendingLabel} />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* File chips */}
      {files.length > 0 && (
        <div className="px-6 pt-2">
          <div className="max-w-3xl mx-auto flex flex-wrap gap-2">
            {files.map((f, i) => (
              <div
                key={`${f.name}-${i}`}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400/80 text-xs"
              >
                <FileText className="w-3 h-3" />
                <span className="max-w-[160px] truncate">{f.name}</span>
                <button
                  onClick={() => removeFile(i)}
                  className="hover:text-amber-400 transition-colors cursor-pointer"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="px-6 py-4 border-t border-white/[0.06]">
        <div className="max-w-3xl mx-auto relative flex items-end gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={sending}
            className="p-3 rounded-xl text-white/20 hover:text-amber-400 hover:bg-amber-500/10 transition-colors disabled:opacity-30 cursor-pointer shrink-0"
            title="Attach CSV file"
          >
            <Paperclip className="w-4 h-4" />
          </button>
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={files.length > 0 ? "Add a message or just send the files..." : "Ask about your finances..."}
              rows={1}
              disabled={sending}
              className="w-full resize-none px-4 py-3 pr-12 bg-white/[0.04] border border-white/[0.08] rounded-xl text-white/70 text-sm placeholder:text-white/15 focus:outline-none focus:border-amber-500/30 disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={(!input.trim() && files.length === 0) || sending}
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
    </div>
  );
}
