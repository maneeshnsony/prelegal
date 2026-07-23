"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { DraftSummary, createDocument, listDocuments } from "@/lib/api";
import { getSession } from "@/lib/session";

function formatUpdatedAt(value: string): string {
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default function DocumentsPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DraftSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (!getSession()) {
      router.replace("/login");
      return;
    }
    listDocuments()
      .then(setDocuments)
      .catch(() => setError("Couldn't load your documents. Please refresh to try again."));
  }, [router]);

  async function handleCreate() {
    setIsCreating(true);
    setError(null);
    try {
      const draft = await createDocument();
      router.push(`/documents/view?id=${draft.id}`);
    } catch {
      setError("Something went wrong creating a new document. Please try again.");
      setIsCreating(false);
    }
  }

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[#032147]">My Documents</h1>
          <p className="text-sm text-gray-600">
            Pick up a document you already started, or create a new one.
          </p>
        </div>
        <button
          type="button"
          onClick={handleCreate}
          disabled={isCreating}
          className="rounded-md bg-[#753991] px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isCreating ? "Creating..." : "New document"}
        </button>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {documents === null ? (
        <p className="text-sm text-gray-500">Loading...</p>
      ) : documents.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-10 text-center">
          <p className="mb-4 text-sm text-gray-600">
            You haven&apos;t created any documents yet — start one now.
          </p>
          <button
            type="button"
            onClick={handleCreate}
            disabled={isCreating}
            className="rounded-md bg-[#753991] px-4 py-2 text-sm font-semibold text-white hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isCreating ? "Creating..." : "New document"}
          </button>
        </div>
      ) : (
        <ul className="space-y-3">
          {documents.map((doc) => (
            <li key={doc.id}>
              <button
                type="button"
                onClick={() => router.push(`/documents/view?id=${doc.id}`)}
                className="flex w-full items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3 text-left hover:border-[#209dd7]"
              >
                <div>
                  <p className="font-medium text-[#032147]">{doc.title}</p>
                  <p className="text-xs text-gray-500">
                    Updated {formatUpdatedAt(doc.updated_at)}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    doc.is_complete
                      ? "bg-green-100 text-green-800"
                      : "bg-[#ecad0a]/20 text-[#032147]"
                  }`}
                >
                  {doc.is_complete ? "Complete" : "In progress"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </AppShell>
  );
}
