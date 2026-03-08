"use client";

import { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
  lastUpdatedShort: string;
}

export default function MessageBubble({
  message,
  lastUpdatedShort,
}: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`
          max-w-[85%] md:max-w-[70%] rounded-2xl px-4 py-3
          ${
            isUser
              ? "bg-[#007AFF] text-white"
              : "bg-[#f5f5f7] text-[#1d1d1f] border border-[#e5e5e7]"
          }
        `}
      >
        <p className="text-[14px] leading-relaxed whitespace-pre-wrap">
          {message.content}
        </p>

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 pt-2 border-t border-[#d2d2d7]">
            {message.citations.map((url, i) => (
              <p key={i} className="text-[11px] text-[#86868b]">
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#007AFF] hover:underline"
                >
                  Source
                </a>
                <span className="mx-1">·</span>
                <span>Last updated: {lastUpdatedShort}</span>
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
