"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";

export function CopyReportButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (typeof navigator === "undefined" || !navigator.clipboard) return;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <Button
      type="button"
      size="sm"
      variant="outline"
      onClick={handleCopy}
      className="cursor-pointer"
    >
      {copied ? (
        <Check className="mr-1 h-3.5 w-3.5 text-success" aria-hidden />
      ) : (
        <Copy className="mr-1 h-3.5 w-3.5" aria-hidden />
      )}
      {copied ? "已复制" : "复制报告"}
    </Button>
  );
}
