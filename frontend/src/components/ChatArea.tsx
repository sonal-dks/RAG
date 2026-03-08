"use client";

import { useRef, useEffect, useState } from "react";
import { Conversation } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import WelcomeScreen from "./WelcomeScreen";

interface ChatAreaProps {
  conversation: Conversation | null;
  fundList: string[];
  activeFunds: string[];
  lastUpdatedShort: string;
  sampleQuestions: string[];
  isLoading: boolean;
  onToggleFund: (fund: string) => void;
  onClearFunds: () => void;
  onSend: (text: string) => void;
  onToggleSidebar: () => void;
}

export default function ChatArea({
  conversation,
  fundList,
  activeFunds,
  lastUpdatedShort,
  sampleQuestions,
  isLoading,
  onToggleFund,
  onClearFunds,
  onSend,
  onToggleSidebar,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const messages = conversation?.messages ?? [];
  const isNewChat = messages.length === 0;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSubmit = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    onSend(text);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <main className="flex-1 flex flex-col h-screen min-w-0">
      {/* Header bar */}
      <header className="flex items-center gap-3 px-4 md:px-6 py-3 border-b border-[#e5e5e7] bg-white/80 backdrop-blur-sm shrink-0">
        <button
          onClick={onToggleSidebar}
          className="md:hidden p-1.5 rounded-lg hover:bg-[#f5f5f7] text-[#1d1d1f]"
          aria-label="Toggle sidebar"
        >
          <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <span className="text-[16px]">📊</span>
        <h1 className="text-[15px] font-semibold text-[#1d1d1f] tracking-tight">
          Mutual Fund RAG Chatbot
        </h1>
      </header>

      {/* Fund multi-select */}
      <div className="px-4 md:px-6 py-2.5 border-b border-[#e5e5e7] bg-white shrink-0">
        <div className="flex items-center gap-2 flex-wrap" ref={dropdownRef}>
          <div className="relative">
            <button
              onClick={() => setDropdownOpen((o) => !o)}
              className="text-[13px] text-[#1d1d1f] bg-[#f5f5f7]
                         border border-[#d2d2d7] rounded-lg px-3 py-1.5
                         hover:bg-[#e8e8ed] transition-colors flex items-center gap-1.5"
            >
              <span>Select funds</span>
              <svg
                width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"
                className={`transition-transform ${dropdownOpen ? "rotate-180" : ""}`}
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </button>

            {dropdownOpen && (
              <div className="absolute top-full left-0 mt-1 w-72 max-h-64 overflow-y-auto
                              bg-white border border-[#d2d2d7] rounded-xl shadow-lg z-50">
                {fundList.map((f) => {
                  const isSelected = activeFunds.includes(f);
                  return (
                    <button
                      key={f}
                      onClick={() => onToggleFund(f)}
                      className={`w-full text-left px-3 py-2 text-[13px] flex items-center gap-2
                                  hover:bg-[#f5f5f7] transition-colors
                                  ${isSelected ? "text-[#007AFF] font-medium" : "text-[#1d1d1f]"}`}
                    >
                      <span className={`w-4 h-4 rounded border flex items-center justify-center shrink-0
                                        ${isSelected ? "bg-[#007AFF] border-[#007AFF]" : "border-[#d2d2d7]"}`}>
                        {isSelected && (
                          <svg width="10" height="10" fill="none" stroke="white" strokeWidth="2.5" viewBox="0 0 24 24">
                            <path d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </span>
                      {f}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {activeFunds.length > 0 && (
            <button
              onClick={onClearFunds}
              className="text-[12px] text-[#86868b] hover:text-[#1d1d1f] px-2 py-1
                         rounded-lg hover:bg-[#f5f5f7] transition-colors"
            >
              ✕ Clear all
            </button>
          )}
        </div>

        {/* Selected fund chips */}
        {activeFunds.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {activeFunds.map((f) => (
              <span
                key={f}
                className="inline-flex items-center gap-1 text-[12px] font-medium
                           text-[#007AFF] bg-[#007AFF]/10 rounded-full px-2.5 py-1"
              >
                {f}
                <button
                  onClick={() => onToggleFund(f)}
                  className="hover:text-[#0066d6] ml-0.5"
                  aria-label={`Remove ${f}`}
                >
                  ✕
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Messages or Welcome */}
      {isNewChat ? (
        <WelcomeScreen sampleQuestions={sampleQuestions} onAsk={onSend} />
      ) : (
        <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4">
          {messages.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              lastUpdatedShort={lastUpdatedShort}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-[#f5f5f7] border border-[#e5e5e7] rounded-2xl px-4 py-3">
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#86868b] animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 rounded-full bg-[#86868b] animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 rounded-full bg-[#86868b] animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Input */}
      <div className="shrink-0 border-t border-[#e5e5e7] bg-white px-4 md:px-6 py-3">
        <div className="flex items-end gap-2 max-w-3xl mx-auto">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Quant Mutual Funds…"
            rows={1}
            className="flex-1 resize-none text-[14px] text-[#1d1d1f] bg-[#f5f5f7]
                       border border-[#d2d2d7] rounded-xl px-4 py-2.5
                       focus:outline-none focus:ring-2 focus:ring-[#007AFF]/40
                       placeholder:text-[#86868b]"
            style={{ maxHeight: "120px" }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = "auto";
              target.style.height = Math.min(target.scrollHeight, 120) + "px";
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || isLoading}
            className="shrink-0 w-9 h-9 flex items-center justify-center rounded-xl
                       bg-[#007AFF] text-white hover:bg-[#0066d6]
                       disabled:opacity-40 disabled:cursor-not-allowed
                       transition-colors"
            aria-label="Send"
          >
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </main>
  );
}
