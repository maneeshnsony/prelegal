const DISCLAIMER_TEXT =
  "This document was generated with AI assistance and is provided as a draft only. " +
  "It does not constitute legal advice and should be reviewed by a qualified attorney " +
  "before use or execution.";

interface DisclaimerBannerProps {
  variant?: "footer" | "inline";
  text?: string;
}

export default function DisclaimerBanner({ variant = "footer", text }: DisclaimerBannerProps) {
  const className =
    variant === "footer"
      ? "border-t border-gray-200 bg-gray-50 px-6 py-3 text-center text-xs text-[#888888]"
      : "rounded-md border border-[#ecad0a]/40 bg-yellow-50 px-4 py-2 text-xs text-[#888888]";
  return <p className={className}>{text ?? DISCLAIMER_TEXT}</p>;
}
