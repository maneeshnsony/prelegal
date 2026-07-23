"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import AppShell from "@/components/AppShell";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import DocumentChat from "@/components/DocumentChat";
import DocumentPreview from "@/components/DocumentPreview";
import { buildDocumentPdf } from "@/lib/documentPdf";
import { RenderedDocument } from "@/lib/documentTypes";
import { ChatMessage, DraftResponse, getDraft, getRenderedDraft, sendChatMessage } from "@/lib/api";
import { getSession } from "@/lib/session";

function fileNameFor(rendered: RenderedDocument | null): string {
  if (!rendered) return "document";
  const identifyingValue = rendered.cover_fields.find((f) => f.value.trim() !== "")?.value ?? "";
  const suffix = identifyingValue ? `-${identifyingValue}` : "";
  return `${rendered.document_type}${suffix}`.replace(/\s+/g, "-");
}

function DocumentViewContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const draftId = Number(searchParams.get("id"));

  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [rendered, setRendered] = useState<RenderedDocument | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    if (!getSession()) {
      router.replace("/login");
      return;
    }
    if (!draftId) {
      router.replace("/documents");
      return;
    }

    getDraft(draftId)
      .then(async (d) => {
        setDraft(d);
        setMessages(d.messages);
        if (d.document_type) {
          const doc = await getRenderedDraft(draftId);
          setRendered(doc);
        }
      })
      .catch(() => setError("Couldn't load this document. Please refresh to try again."))
      .finally(() => setIsHydrated(true));
  }, [draftId, router]);

  async function handleSend(message: string) {
    if (!draftId) return;
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setError(null);
    setIsLoading(true);
    try {
      const response = await sendChatMessage(draftId, message);
      setMessages((prev) => [...prev, { role: "assistant", content: response.reply }]);
      setDraft((prev) => ({
        id: draftId,
        document_type: response.document_type,
        fields: response.fields,
        messages: prev?.messages ?? [],
      }));
      if (response.document_type) {
        const doc = await getRenderedDraft(draftId);
        setRendered(doc);
      }
    } catch {
      setError("Something went wrong sending that message. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleDownloadPdf() {
    if (!rendered) return;
    const pdf = buildDocumentPdf(rendered);
    pdf.save(`${fileNameFor(rendered)}.pdf`);
  }

  function handleDownloadText() {
    if (!rendered) return;
    const lines: string[] = [];
    lines.push(rendered.title.toUpperCase());
    lines.push("");
    lines.push("Cover Page");
    lines.push("----------");
    for (const field of rendered.cover_fields) {
      lines.push(`${field.label}: ${field.value || `[${field.label}]`}`);
    }
    lines.push("");
    lines.push("Standard Terms");
    lines.push("--------------");
    for (const p of rendered.paragraphs) {
      lines.push(p.number ? `${p.number}. ${p.title}. ${p.body}` : p.body);
      lines.push("");
    }
    lines.push(rendered.disclaimer);

    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${fileNameFor(rendered)}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  const ready =
    draft?.document_type != null &&
    rendered != null &&
    rendered.cover_fields.every((f) => f.value.trim() !== "");

  return (
    <AppShell>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <button
            type="button"
            onClick={() => router.push("/documents")}
            className="mb-2 text-sm font-medium text-[#209dd7] hover:underline"
          >
            &larr; Back to My Documents
          </button>
          <h1 className="text-xl font-bold text-[#032147]">
            {rendered?.title ?? "Legal Document Creator"}
          </h1>
          <p className="text-sm text-gray-600">
            Chat with the assistant to figure out which document you need and fill in the
            details, then download the completed document once every field is set.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[400px_1fr]">
        <div className="flex flex-col rounded-md border border-gray-200 bg-white p-4">
          {isHydrated && (
            <DocumentChat
              messages={messages}
              onSend={handleSend}
              isLoading={isLoading}
              error={error}
              title={rendered ? `${rendered.title} chat` : "Legal assistant"}
            />
          )}
          {rendered && (
            <>
              <DisclaimerBanner variant="inline" text={rendered.disclaimer} />
              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={!ready}
                className="mt-4 w-full rounded-md bg-[#209dd7] px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download completed document (PDF)
              </button>
              <button
                type="button"
                onClick={handleDownloadText}
                disabled={!ready}
                className="mt-2 w-full rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Download as text (.txt)
              </button>
            </>
          )}
        </div>

        {rendered && (
          <div className="min-w-0">
            <DocumentPreview renderedDocument={rendered} />
          </div>
        )}
      </div>
    </AppShell>
  );
}

export default function DocumentViewPage() {
  return (
    <Suspense fallback={null}>
      <DocumentViewContent />
    </Suspense>
  );
}
