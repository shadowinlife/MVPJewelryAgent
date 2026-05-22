import type { Metadata } from "next";

import { getCurrentUser } from "@/lib/auth";
import { getTierDef, tokenPolicy } from "@/lib/membership";
import type { User } from "@/lib/types/domain";

import { NewCaseWizard } from "./new-case-wizard";

export const metadata: Metadata = {
  title: "新建案例 · 曜齐 YAOQI",
};

interface SearchParams {
  step?: string;
  purpose?: string;
  kind?: string;
}

export default async function NewCasePage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const sp = await searchParams;
  const user = (await getCurrentUser()) as User;
  const tier = getTierDef(user.membership);

  return (
    <NewCaseWizard
      initialStep={sp.step ?? "basics"}
      initialPurpose={sp.purpose ?? ""}
      initialKind={sp.kind ?? ""}
      remainingReports={user.remainingReports}
      monthlyTokens={tier.monthlyTokens}
      tierLabel={tier.name}
      tokenResetDay={tokenPolicy.resetDay}
    />
  );
}
