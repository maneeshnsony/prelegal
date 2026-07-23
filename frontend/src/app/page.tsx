"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NdaChat from "@/components/NdaChat";
import NdaDocument from "@/components/NdaDocument";
import { emptyNdaFormData, NdaFormData, renderPlainTextDocument } from "@/lib/ndaTemplate";
import { buildNdaPdf } from "@/lib/ndaPdf";
import { ChatMessage, getDraft, sendChatMessage } from "@/lib/api";
import { getUserId } from "@/lib/fakeSession";

function fileNameFor(data: { partyAName: string; partyBName: string }, extension: string): string {
  const partyLabel =
    data.partyAName || data.partyBName ? `-${data.partyAName || ""}-${data.partyBName || ""}` : "";
  return `Mutual-NDA${partyLabel}.${extension}`.replace(/\s+/g, "-");
}

function isComplete(data: NdaFormData): boolean {
  return Object.values(data).every((value) => value.trim() !== "");
}

export default function Home() {
  const [data, setData] = useState(emptyNdaFormData);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const userId = getUserId();
    if (!userId) {
      router.replace("/login");
      return;
    }

    getDraft(userId)
      .then((draft) => {
        setData(draft.fields);
        setMessages(draft.messages);
      })
      .catch(() => setError("Couldn't load your NDA draft. Please refresh to try again."))
      .finally(() => setIsHydrated(true));
  }, [router]);

  async function handleSend(message: string) {
    const userId = getUserId();
    if (!userId) {
      router.replace("/login");
      return;
    }

    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setError(null);
    setIsLoading(true);
    try {
      const response = await sendChatMessage(userId, message);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      setData(response.fields);
    } catch {
      setError("Something went wrong sending that message. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleDownloadPdf() {
    const doc = buildNdaPdf(data);
    doc.save(fileNameFor(data, "pdf"));
  }

  function handleDownloadText() {
    const text = renderPlainTextDocument(data);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileNameFor(data, "txt");
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  const ready = isComplete(data);

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4">
        <h1 className="text-xl font-bold text-gray-900">Mutual NDA Creator</h1>
        <p className="text-sm text-gray-600">
          Chat with the assistant to fill in the details, then download the completed
          document once every field is set.
        </p>
      </header>

      <main className="mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 gap-6 px-6 py-8 lg:grid-cols-[400px_1fr]">
        <div className="flex flex-col rounded-md border border-gray-200 bg-white p-4">
          {isHydrated && (
            <NdaChat
              messages={messages}
              onSend={handleSend}
              isLoading={isLoading}
              error={error}
            />
          )}
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={!ready}
            className="mt-4 w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Download completed NDA (PDF)
          </button>
          <button
            type="button"
            onClick={handleDownloadText}
            disabled={!ready}
            className="mt-2 w-full rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Download as text (.txt)
          </button>
        </div>

        <div className="min-w-0">
          <NdaDocument data={data} />
        </div>
      </main>
    </div>
  );
}
