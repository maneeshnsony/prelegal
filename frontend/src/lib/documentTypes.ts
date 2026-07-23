export interface RenderedField {
  field_id: string;
  label: string;
  value: string;
}

export interface RenderedParagraph {
  number: number;
  title: string;
  body: string;
}

export interface RenderedDocument {
  document_type: string;
  title: string;
  cover_fields: RenderedField[];
  paragraphs: RenderedParagraph[];
  disclaimer: string;
}
