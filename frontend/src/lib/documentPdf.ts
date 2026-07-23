import { jsPDF } from "jspdf";
import { RenderedDocument } from "@/lib/documentTypes";

const PAGE_MARGIN = 56;
const LINE_HEIGHT = 16;
const BODY_FONT_SIZE = 10;

function stripBoldMarkers(text: string): string {
  return text.replace(/\*\*(.+?)\*\*/g, "$1");
}

export function buildDocumentPdf(renderedDocument: RenderedDocument): jsPDF {
  const pdf = new jsPDF({ unit: "pt", format: "letter" });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const contentWidth = pageWidth - PAGE_MARGIN * 2;
  let y = PAGE_MARGIN;

  function ensureSpace(nextLineHeight: number) {
    if (y + nextLineHeight > pageHeight - PAGE_MARGIN) {
      pdf.addPage();
      y = PAGE_MARGIN;
    }
  }

  function writeLines(text: string, options: { bold?: boolean; size?: number } = {}) {
    pdf.setFont("helvetica", options.bold ? "bold" : "normal");
    pdf.setFontSize(options.size ?? BODY_FONT_SIZE);
    const lines: string[] = pdf.splitTextToSize(text, contentWidth);
    for (const line of lines) {
      ensureSpace(LINE_HEIGHT);
      pdf.text(line, PAGE_MARGIN, y);
      y += LINE_HEIGHT;
    }
  }

  writeLines(renderedDocument.title.toUpperCase(), { bold: true, size: 16 });
  y += 8;

  writeLines("Cover Page", { bold: true, size: 12 });
  y += 4;

  for (const field of renderedDocument.cover_fields) {
    writeLines(`${field.label}: ${field.value || `[${field.label}]`}`);
  }
  y += 12;

  writeLines("Standard Terms", { bold: true, size: 12 });
  y += 4;

  for (const p of renderedDocument.paragraphs) {
    if (p.number) {
      writeLines(`${p.number}. ${p.title}. ${stripBoldMarkers(p.body)}`);
    } else {
      writeLines(stripBoldMarkers(p.body));
    }
    y += 8;
  }

  y += 8;
  writeLines(renderedDocument.disclaimer, { size: 8 });

  return pdf;
}
