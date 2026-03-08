"use client";

interface WelcomeScreenProps {
  sampleQuestions: string[];
  onAsk: (q: string) => void;
}

export default function WelcomeScreen({
  sampleQuestions,
  onAsk,
}: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <h1 className="text-2xl font-semibold text-[#1d1d1f] tracking-tight">
          What would you like to know?
        </h1>
        <p className="text-[14px] text-[#86868b] mt-2 leading-relaxed">
          Ask factual questions about Quant Mutual Funds — NAV, expense ratio,
          holdings, fund managers, and more. Select a fund from the dropdown
          above, or mention it in your question.
        </p>

        <div className="mt-6 space-y-2">
          <p className="text-[13px] font-medium text-[#1d1d1f]">Try asking:</p>
          {sampleQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => onAsk(q)}
              className="w-full text-left px-4 py-2.5 rounded-xl text-[13px]
                         text-[#1d1d1f] bg-[#f5f5f7] border border-[#e5e5e7]
                         hover:bg-[#e8e8ed] transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        <p className="text-[12px] text-[#86868b] mt-5">
          📌 Facts-only. No investment advice.
        </p>
      </div>
    </div>
  );
}
