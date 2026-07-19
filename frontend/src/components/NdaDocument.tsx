import { Fragment } from "react";
import { ATTRIBUTION, NdaFormData, getStandardTermsParagraphs } from "@/lib/ndaTemplate";

interface NdaDocumentProps {
  data: NdaFormData;
}

function renderInlineBold(text: string) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : <Fragment key={i}>{part}</Fragment>
  );
}

function CoverField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-900">{value || `[${label}]`}</dd>
    </div>
  );
}

export default function NdaDocument({ data }: NdaDocumentProps) {
  const paragraphs = getStandardTermsParagraphs(data);

  return (
    <article id="nda-document" className="prose prose-sm max-w-none rounded-md border border-gray-200 bg-white p-6 text-gray-900">
      <h1 className="text-xl font-bold text-gray-900">Mutual Non-Disclosure Agreement</h1>

      <h2 className="mt-4 text-base font-semibold text-gray-900">Cover Page</h2>
      <dl className="mb-6 grid grid-cols-2 gap-3 rounded-md bg-gray-50 p-4">
        <CoverField label="Party A Name" value={data.partyAName} />
        <CoverField label="Party B Name" value={data.partyBName} />
        <CoverField label="Effective Date" value={data.effectiveDate} />
        <CoverField label="Purpose" value={data.purpose} />
        <CoverField label="MNDA Term" value={data.mndaTerm} />
        <CoverField label="Term of Confidentiality" value={data.termOfConfidentiality} />
        <CoverField label="Governing Law" value={data.governingLaw} />
        <CoverField label="Jurisdiction" value={data.jurisdiction} />
      </dl>

      <h2 className="text-base font-semibold text-gray-900">Standard Terms</h2>
      <ol className="list-none space-y-3 pl-0">
        {paragraphs.map((p, i) => (
          <li key={i} className="text-sm leading-relaxed text-gray-800">
            {p.number ? (
              <>
                <span className="font-semibold">
                  {p.number}. {p.title}.
                </span>{" "}
                {renderInlineBold(p.body)}
              </>
            ) : (
              renderInlineBold(p.body)
            )}
          </li>
        ))}
      </ol>

      <p className="mt-6 text-xs text-gray-500">{ATTRIBUTION}</p>
    </article>
  );
}
