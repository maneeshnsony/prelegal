"use client";

import { NdaFormData } from "@/lib/ndaTemplate";

interface Field {
  key: keyof NdaFormData;
  label: string;
  placeholder: string;
}

const FIELDS: Field[] = [
  { key: "partyAName", label: "Party A Name", placeholder: "Acme Inc." },
  { key: "partyBName", label: "Party B Name", placeholder: "Globex Corporation" },
  { key: "effectiveDate", label: "Effective Date", placeholder: "January 1, 2026" },
  {
    key: "purpose",
    label: "Purpose",
    placeholder: "evaluating a potential business relationship",
  },
  { key: "mndaTerm", label: "MNDA Term", placeholder: "2 years from the Effective Date" },
  {
    key: "termOfConfidentiality",
    label: "Term of Confidentiality",
    placeholder: "3 years from disclosure",
  },
  { key: "governingLaw", label: "Governing Law", placeholder: "Delaware" },
  { key: "jurisdiction", label: "Jurisdiction", placeholder: "Delaware" },
];

interface NdaFormProps {
  data: NdaFormData;
  onChange: (data: NdaFormData) => void;
}

export default function NdaForm({ data, onChange }: NdaFormProps) {
  function handleChange(key: keyof NdaFormData, value: string) {
    onChange({ ...data, [key]: value });
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={(e) => e.preventDefault()}>
      <h2 className="text-lg font-semibold text-gray-900">Mutual NDA details</h2>
      {FIELDS.map((field) => (
        <label key={field.key} className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-gray-700">{field.label}</span>
          <input
            type="text"
            value={data[field.key]}
            placeholder={field.placeholder}
            onChange={(e) => handleChange(field.key, e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </label>
      ))}
    </form>
  );
}
