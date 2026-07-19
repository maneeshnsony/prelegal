"use client";

import { useState } from "react";
import NdaForm from "@/components/NdaForm";
import NdaDocument from "@/components/NdaDocument";
import { emptyNdaFormData, renderPlainTextDocument } from "@/lib/ndaTemplate";

export default function Home() {
  const [data, setData] = useState(emptyNdaFormData);

  function handleDownload() {
    const text = renderPlainTextDocument(data);
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const partyLabel = data.partyAName || data.partyBName ? `-${data.partyAName || ""}-${data.partyBName || ""}` : "";
    const a = document.createElement("a");
    a.href = url;
    a.download = `Mutual-NDA${partyLabel}.txt`.replace(/\s+/g, "-");
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
            onClick={handleDownload}
            className="mt-6 w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Download completed NDA
          </button>
        </div>

        <div className="min-w-0">
          <NdaDocument data={data} />
        </div>
      </main>
    </div>
  );
}
