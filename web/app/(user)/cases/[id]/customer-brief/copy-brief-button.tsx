"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";

export function CopyBriefButton({ text }: { text: string }) {
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
      onClick={handleCopy}
      className="cursor-pointer"
      variant="outline"
    >
      {copied ? (
        <Check className="mr-1 h-4 w-4 text-success" aria-hidden />
      ) : (
        <Copy className="mr-1 h-4 w-4" aria-hidden />
      )}
      {copied ? "已复制简洁版" : "复制简洁版文本"}
    </Button>
  );
}
