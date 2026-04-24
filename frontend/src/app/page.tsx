"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles, ShieldCheck, Zap, ArrowUp, Moon, Sun, Monitor, MessageSquare } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const API_URL = "https://mutualfund-4wrg.onrender.com/api/chat";

const SUGGESTIONS = [
  "What is the expense ratio of HDFC Flexi Cap?",
  "What is the lock-in period for ELSS funds?",
  "How do I download my capital gains statement?",
  "Minimum SIP amount for Nifty 50 ETF?"
];

interface Message {
  role: "user" | "bot";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", content: "Hello! I am **FundIntel**. I analyze verified AMC data to answer factual queries like Expense Ratios, NAVs, and Exit Loads. How can I assist you today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (text: string) => {
    const query = text.trim();
    if (!query || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "bot", content: data.response }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "bot", content: "⚠️ Connection to RAG engine lost. Ensure Phase 07 Backend is deployed with CORS enabled." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background flex flex-col items-center">
      {/* --- Top Nav --- */}
      <nav className="w-full flex justify-between items-center px-6 py-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <MessageSquare className="text-white w-5 h-5" />
          </div>
          <span className="text-lg font-bold text-[#006760]">FundIntel</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-[#e6f0ef] px-3 py-1.5 rounded-full">
            <div className="w-2 h-2 bg-[#006760] rounded-full animate-pulse" />
            <span className="text-[10px] font-bold text-[#006760] uppercase tracking-wider">Online</span>
          </div>
          <button className="p-2 hover:bg-slate-100 rounded-full transition-colors">
            <Moon className="w-4 h-4 text-slate-600" />
          </button>
        </div>
      </nav>

      {/* --- Body Container --- */}
      <div className="flex-1 w-full max-w-2xl flex flex-col px-4 pt-16">
        
        {/* Centered Hero */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="w-16 h-16 bg-[#006760] rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-[#006760]/20">
            <MessageSquare className="text-white w-8 h-8" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-[#1a1a1a] tracking-tight mb-4">
            What would you like <br /> to know?
          </h1>
          <p className="text-slate-500 text-base max-w-md mx-auto">
            Ask about expense ratios, exit loads, SIP minimums, lock-in periods — all sourced from official documents.
          </p>
        </motion.div>

        {/* Suggestion Chips */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="flex flex-col gap-2 mb-12"
        >
          {SUGGESTIONS.map((text, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(text)}
              className="w-full p-4 bg-white border border-slate-200 rounded-2xl text-sm text-slate-700 hover:border-[#006760] hover:bg-[#e6f0ef]/30 transition-all text-center font-medium"
            >
              {text}
            </button>
          ))}
        </motion.div>

        {/* Chat History Area */}
        <div 
          ref={scrollRef}
          className="flex-1 space-y-6 pb-32 overflow-y-auto custom-scrollbar"
        >
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                  "flex flex-col",
                  msg.role === "user" ? "items-end" : "items-start"
                )}
              >
                <div className={cn(
                  "max-w-[90%] px-5 py-3.5 rounded-2xl text-sm leading-relaxed",
                  msg.role === "user" 
                    ? "bg-[#006760] text-white shadow-lg" 
                    : "bg-white border border-slate-200 text-slate-800"
                )}>
                   {msg.content.split("**").map((part, index) => (
                    index % 2 === 1 ? <b key={index} className="font-bold">{part}</b> : part
                  ))}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {loading && (
            <div className="flex gap-1.5 p-2">
              <div className="w-1.5 h-1.5 bg-[#006760] rounded-full animate-bounce [animation-delay:-0.3s]" />
              <div className="w-1.5 h-1.5 bg-[#006760] rounded-full animate-bounce [animation-delay:-0.15s]" />
              <div className="w-1.5 h-1.5 bg-[#006760] rounded-full animate-bounce" />
            </div>
          )}
        </div>
      </div>

      {/* --- Floating Bottom Bar --- */}
      <div className="fixed bottom-0 w-full max-w-2xl px-4 pb-8 bg-gradient-to-t from-background via-background/90 to-transparent pt-10">
        <div className="relative group">
          <div className="absolute -inset-1 bg-[#006760]/10 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition-opacity" />
          <div className="relative bg-white border border-slate-200 rounded-2xl p-2.5 flex items-center shadow-xl">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend(input)}
              placeholder="Ask a mutual fund question..."
              className="flex-1 bg-transparent border-none outline-none text-slate-900 placeholder:text-slate-400 px-4 py-2"
            />
            <button
              onClick={() => handleSend(input)}
              disabled={loading || !input.trim()}
              className="bg-[#006760] hover:bg-[#005a54] text-white w-10 h-10 rounded-xl flex items-center justify-center transition-all disabled:opacity-50 active:scale-95"
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </div>
        </div>
        <p className="text-center text-[10px] text-slate-400 mt-4 uppercase tracking-[0.15em] font-medium">
          Powered by FundIntel RAG Engine • Verified Facts Only
        </p>
      </div>
    </main>
  );
}
