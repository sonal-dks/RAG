export const SAMPLE_QUESTIONS = [
  "What is the expense ratio of Quant Small Cap Fund?",
  "What are the top holdings of Quant Mid Cap Fund?",
  "What is the minimum investment for Quant ELSS?",
  "Who manages Quant Flexi Cap Fund?",
  "What is the risk level of Quant Infrastructure Fund?",
  "Tell me about Quant Large Cap Fund.",
  "What is the NAV of Quant ELSS Tax Saver Fund?",
  "What is the fund size of Quant Small Cap Fund?",
  "What are the exit load rules for Quant Flexi Cap?",
  "What is the minimum SIP for Quant Aggressive Hybrid Fund?",
  "What sectors does Quant Mid Cap Fund invest in?",
  "What is the lock-in period for Quant ELSS Tax Saver Fund?",
  "What is the AUM of Quant Focused Fund?",
  "What is the minimum investment for Quant Multi Cap Fund?",
  "Tell me about Quant ESG Integration Strategy Fund.",
  "What is the NAV of Quant Small Cap Fund?",
  "What are the top 5 holdings of Quant Infrastructure Fund?",
];

export function getRandomQuestions(count = 3): string[] {
  const shuffled = [...SAMPLE_QUESTIONS].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
}

export function formatLastUpdated(
  info: { last_updated_ist?: string | null; last_updated_utc?: string | null; status?: string } | null,
  short = false
): string {
  if (!info || info.status === "never_run") return "Data not yet refreshed";
  const ts = info.last_updated_ist || info.last_updated_utc;
  if (!ts) return "Data not yet refreshed";
  try {
    const dt = new Date(ts);
    if (short) {
      return dt.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      });
    }
    return (
      dt.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }) +
      ", " +
      dt.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }) +
      " IST"
    );
  } catch {
    return ts;
  }
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}
