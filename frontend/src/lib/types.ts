export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: string[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  active_funds: string[];
  created_at: string;
  updated_at: string;
}

export interface QueryResponse {
  answer: string;
  citations: string[];
  conversation_id: string;
}

export interface LastUpdated {
  last_updated_utc: string | null;
  last_updated_ist: string | null;
  chunks_indexed: number;
  status: string;
}
