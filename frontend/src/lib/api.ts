import { QueryResponse, LastUpdated } from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendQuery(
  query: string,
  activeFunds?: string[],
  conversationId?: string
): Promise<QueryResponse> {
  const body: Record<string, unknown> = { query };
  if (activeFunds && activeFunds.length > 0) body.active_funds = activeFunds;
  if (conversationId) body.conversation_id = conversationId;

  const res = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Server error (${res.status}): ${text}`);
  }
  return res.json();
}

export async function fetchMutualFunds(): Promise<string[]> {
  const res = await fetch(`${API_URL}/mutual-funds`);
  if (!res.ok) throw new Error(`Failed to fetch funds (${res.status})`);
  return res.json();
}

export async function fetchLastUpdated(): Promise<LastUpdated> {
  const res = await fetch(`${API_URL}/last-updated`);
  if (!res.ok) throw new Error(`Failed to fetch last-updated (${res.status})`);
  return res.json();
}
