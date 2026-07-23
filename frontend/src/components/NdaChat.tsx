"use client";

import { useEffect, useRef, useState } from "react";
import { ChatMessage } from "@/lib/api";

interface NdaChatProps {
  messages: ChatMessage[];
  onSend: (message: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export default function NdaChat({ messages, onSend, isLoading, error }: NdaChatProps) {
  const [input, setInput] = useState("");
  const listEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    setInput("");
    await onSend(trimmed);
  }

  return (
    <div className="flex h-full flex-col">
      <h2 className="mb-3 text-lg font-semibold text-gray-900">Mutual NDA chat</h2>
      <div className="flex-1 space-y-3 overflow-y-auto rounded-md border border-gray-200 bg-gray-50 p-3">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-md px-3 py-2 text-sm ${
                message.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-900 border border-gray-200"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-500">
              Thinking...
            </div>
          </div>
        )}
        <div ref={listEndRef} />
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your answer..."
          disabled={isLoading}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="rounded-md bg-purple-700 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </div>
  );
}
