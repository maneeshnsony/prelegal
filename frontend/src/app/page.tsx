"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import NdaForm from "@/components/NdaForm";
import NdaDocument from "@/components/NdaDocument";
import { emptyNdaFormData, renderPlainTextDocument } from "@/lib/ndaTemplate";
import { buildNdaPdf } from "@/lib/ndaPdf";
import { hasFakeSession } from "@/lib/fakeSession";

function fileNameFor(data: { partyAName: string; partyBName: string }, extension: string): string {
  const partyLabel =
    data.partyAName || data.partyBName ? `-${data.partyAName || ""}-${data.partyBName || ""}` : "";
  return `Mutual-NDA${partyLabel}.${extension}`.replace(/\s+/g, "-");
}

export default function Home() {
  const [data, setData] = useState(emptyNdaFormData);
  const router = useRouter();

  useEffect(() => {
    if (!hasFakeSession()) {
      router.replace("/login");
    }
  }, [router]);

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

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50">
      <header className="border-b border-gray-200 bg-white px-6 py-4">
        <h1 className="text-xl font-bold text-gray-900">Mutual NDA Creator</h1>
        <p className="text-sm text-gray-600">
          Fill in the details below to generate a Mutual Non-Disclosure Agreement, then
          download the completed document.
        </p>
      </header>

      <main className="mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 gap-6 px-6 py-8 lg:grid-cols-[360px_1fr]">
        <div className="rounded-md border border-gray-200 bg-white p-4">
          <NdaForm data={data} onChange={setData} />
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="mt-6 w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Download completed NDA (PDF)
          </button>
          <button
            type="button"
            onClick={handleDownloadText}
            className="mt-2 w-full rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
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
