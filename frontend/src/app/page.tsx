"use client";

import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import ChatArea from "@/components/ChatArea";
import { sendQuery, fetchMutualFunds, fetchLastUpdated } from "@/lib/api";
import { Conversation, LastUpdated, Message } from "@/lib/types";
import {
  getRandomQuestions,
  formatLastUpdated,
  generateId,
} from "@/lib/constants";

const STORAGE_KEY = "mf-rag-conversations";

function loadConversations(): Record<string, Conversation> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const data = JSON.parse(raw) as Record<string, Conversation>;
    // Migrate old single active_fund → active_funds array
    for (const conv of Object.values(data)) {
      if (!Array.isArray(conv.active_funds)) {
        const old = (conv as unknown as { active_fund?: string | null }).active_fund;
        conv.active_funds = old ? [old] : [];
      }
    }
    return data;
  } catch {
    return {};
  }
}

function saveConversations(data: Record<string, Conversation>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {}
}

export default function Home() {
  const [conversations, setConversations] = useState<
    Record<string, Conversation>
  >({});
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [fundList, setFundList] = useState<string[]>([]);
  const [lastUpdated, setLastUpdated] = useState<LastUpdated | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sampleQuestions] = useState(() => getRandomQuestions(3));
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setConversations(loadConversations());
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) saveConversations(conversations);
  }, [conversations, hydrated]);

  useEffect(() => {
    fetchMutualFunds().then(setFundList).catch(console.error);
    fetchLastUpdated().then(setLastUpdated).catch(console.error);
  }, []);

  const currentConv = currentId ? conversations[currentId] ?? null : null;
  const activeFunds = currentConv?.active_funds ?? [];
  const lastUpdatedShort = formatLastUpdated(lastUpdated, true);

  const ensureConversation = useCallback((): string => {
    if (currentId && conversations[currentId]) return currentId;
    const id = generateId();
    const now = new Date().toISOString();
    const conv: Conversation = {
      id,
      title: "New chat",
      messages: [],
      active_funds: [],
      created_at: now,
      updated_at: now,
    };
    setConversations((prev) => ({ ...prev, [id]: conv }));
    setCurrentId(id);
    return id;
  }, [currentId, conversations]);

  const handleNewChat = () => setCurrentId(null);

  const handleSwitchConversation = (id: string) => setCurrentId(id);

  const handleToggleFund = (fund: string) => {
    const cid = ensureConversation();
    setConversations((prev) => {
      const conv = prev[cid];
      const current = conv.active_funds ?? [];
      const updated = current.includes(fund)
        ? current.filter((f) => f !== fund)
        : [...current, fund];
      return {
        ...prev,
        [cid]: { ...conv, active_funds: updated, updated_at: new Date().toISOString() },
      };
    });
  };

  const handleClearFunds = () => {
    const cid = ensureConversation();
    setConversations((prev) => ({
      ...prev,
      [cid]: {
        ...prev[cid],
        active_funds: [],
        updated_at: new Date().toISOString(),
      },
    }));
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const cid = ensureConversation();

    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: text.trim(),
      citations: [],
      created_at: new Date().toISOString(),
    };

    setConversations((prev) => {
      const conv = prev[cid] ?? {
        id: cid,
        title: "New chat",
        messages: [],
        active_funds: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      const title =
        conv.messages.length === 0
          ? text.length > 42 ? text.substring(0, 42) + "…" : text
          : conv.title;
      return {
        ...prev,
        [cid]: {
          ...conv,
          title,
          messages: [...conv.messages, userMsg],
          updated_at: new Date().toISOString(),
        },
      };
    });

    setIsLoading(true);

    try {
      const funds = conversations[cid]?.active_funds ?? [];
      const result = await sendQuery(text.trim(), funds, cid);

      const assistantMsg: Message = {
        id: generateId(),
        role: "assistant",
        content: result.answer,
        citations: result.citations ?? [],
        created_at: new Date().toISOString(),
      };

      setConversations((prev) => ({
        ...prev,
        [cid]: {
          ...prev[cid],
          messages: [...prev[cid].messages, assistantMsg],
          updated_at: new Date().toISOString(),
        },
      }));
    } catch (err) {
      const errorMsg: Message = {
        id: generateId(),
        role: "assistant",
        content: `⚠️ ${err instanceof Error ? err.message : "Something went wrong. Please try again."}`,
        citations: [],
        created_at: new Date().toISOString(),
      };
      setConversations((prev) => ({
        ...prev,
        [cid]: {
          ...prev[cid],
          messages: [...prev[cid].messages, errorMsg],
          updated_at: new Date().toISOString(),
        },
      }));
    } finally {
      setIsLoading(false);
    }
  };

  if (!hydrated) {
    return (
      <div className="flex h-screen items-center justify-center bg-white">
        <div className="text-[#86868b] text-sm">Loading…</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      <Sidebar
        conversations={conversations}
        currentId={currentId}
        lastUpdated={lastUpdated}
        onNewChat={handleNewChat}
        onSwitchConversation={handleSwitchConversation}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <ChatArea
        conversation={currentConv}
        fundList={fundList}
        activeFunds={activeFunds}
        lastUpdatedShort={lastUpdatedShort}
        sampleQuestions={sampleQuestions}
        isLoading={isLoading}
        onToggleFund={handleToggleFund}
        onClearFunds={handleClearFunds}
        onSend={handleSend}
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
      />
    </div>
  );
}
