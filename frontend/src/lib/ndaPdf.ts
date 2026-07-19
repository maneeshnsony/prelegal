import { jsPDF } from "jspdf";
import { ATTRIBUTION, NdaFormData, getStandardTermsParagraphs } from "./ndaTemplate";

const PAGE_MARGIN = 56;
const LINE_HEIGHT = 16;
const BODY_FONT_SIZE = 10;

function stripBoldMarkers(text: string): string {
  return text.replace(/\*\*(.+?)\*\*/g, "$1");
}

export function buildNdaPdf(data: NdaFormData): jsPDF {
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const contentWidth = pageWidth - PAGE_MARGIN * 2;
  let y = PAGE_MARGIN;

  function ensureSpace(nextLineHeight: number) {
    if (y + nextLineHeight > pageHeight - PAGE_MARGIN) {
      doc.addPage();
      y = PAGE_MARGIN;
    }
  }

  function writeLines(text: string, options: { bold?: boolean; size?: number } = {}) {
    doc.setFont("helvetica", options.bold ? "bold" : "normal");
    doc.setFontSize(options.size ?? BODY_FONT_SIZE);
    const lines: string[] = doc.splitTextToSize(text, contentWidth);
    for (const line of lines) {
      ensureSpace(LINE_HEIGHT);
      doc.text(line, PAGE_MARGIN, y);
      y += LINE_HEIGHT;
    }
  }

  writeLines("MUTUAL NON-DISCLOSURE AGREEMENT", { bold: true, size: 16 });
  y += 8;

  writeLines("Cover Page", { bold: true, size: 12 });
  y += 4;

  const coverFields: [string, string][] = [
    ["Party A Name", data.partyAName],
    ["Party B Name", data.partyBName],
    ["Effective Date", data.effectiveDate],
    ["Purpose", data.purpose],
    ["MNDA Term", data.mndaTerm],
    ["Term of Confidentiality", data.termOfConfidentiality],
    ["Governing Law", data.governingLaw],
    ["Jurisdiction", data.jurisdiction],
  ];
  for (const [label, value] of coverFields) {
    writeLines(`${label}: ${value || `[${label}]`}`);
  }
  y += 12;

  writeLines("Standard Terms", { bold: true, size: 12 });
  y += 4;

  for (const p of getStandardTermsParagraphs(data)) {
    if (p.number) {
      writeLines(`${p.number}. ${p.title}. ${stripBoldMarkers(p.body)}`);
    } else {
      writeLines(stripBoldMarkers(p.body));
    }
    y += 8;
  }

  y += 8;
  writeLines(ATTRIBUTION, { size: 8 });

  return doc;
}
