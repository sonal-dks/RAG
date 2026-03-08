"use client";

import { Conversation } from "@/lib/types";
import { formatLastUpdated } from "@/lib/constants";
import { LastUpdated } from "@/lib/types";

interface SidebarProps {
  conversations: Record<string, Conversation>;
  currentId: string | null;
  lastUpdated: LastUpdated | null;
  onNewChat: () => void;
  onSwitchConversation: (id: string) => void;
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({
  conversations,
  currentId,
  lastUpdated,
  onNewChat,
  onSwitchConversation,
  open,
  onClose,
}: SidebarProps) {
  const convList = Object.values(conversations)
    .filter((c) => c.messages.length > 0)
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/20 backdrop-blur-sm md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed z-40 top-0 left-0 h-full w-72 flex-shrink-0
          bg-[#f5f5f7] border-r border-[#d2d2d7]
          flex flex-col transition-transform duration-200
          md:relative md:translate-x-0
          ${open ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Header */}
        <div className="p-4 pb-2">
          <h2 className="text-[15px] font-semibold text-[#1d1d1f]">
            📊 Quant MF Facts
          </h2>
          <p className="text-[12px] text-[#86868b] mt-0.5">
            Facts-only assistant for Quant Mutual Funds
          </p>
          <p className="text-[11px] text-[#86868b] mt-1">
            {formatLastUpdated(lastUpdated)}
          </p>
        </div>

        <hr className="border-[#d2d2d7] mx-4" />

        {/* New Chat */}
        <div className="px-4 pt-3 pb-2">
          <button
            onClick={() => {
              onNewChat();
              onClose();
            }}
            className="w-full py-2 px-4 rounded-xl text-[13px] font-medium
                       bg-[#007AFF] text-white hover:bg-[#0066d6]
                       transition-colors"
          >
            + New Chat
          </button>
        </div>

        {/* Conversations */}
        <div className="px-4 pt-1 pb-1">
          <p className="text-[12px] font-semibold text-[#1d1d1f]">
            Conversations
          </p>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-4">
          {convList.length === 0 ? (
            <p className="text-[12px] text-[#86868b] px-2 mt-2">
              No conversations yet
            </p>
          ) : (
            convList.map((conv) => {
              const isCurrent = conv.id === currentId;
              const fundTag = conv.active_funds?.length
                ? ` · ${conv.active_funds.length} fund${conv.active_funds.length > 1 ? "s" : ""}`
                : "";
              return (
                <button
                  key={conv.id}
                  onClick={() => {
                    onSwitchConversation(conv.id);
                    onClose();
                  }}
                  disabled={isCurrent}
                  className={`
                    w-full text-left px-3 py-2 rounded-lg text-[13px] mb-0.5
                    transition-colors truncate
                    ${
                      isCurrent
                        ? "bg-[#e8e8ed] text-[#1d1d1f] font-medium"
                        : "text-[#1d1d1f] hover:bg-[#e8e8ed]"
                    }
                  `}
                >
                  {conv.title}
                  {fundTag && (
                    <span className="text-[#86868b] text-[11px]">
                      {fundTag}
                    </span>
                  )}
                </button>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
}
