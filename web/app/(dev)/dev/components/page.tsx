import { Button } from "@/components/ui/button";
import {
  BrandLogo,
  DisclaimerNote,
  LockedCard,
  MobileBottomNav,
  MockBadge,
  StatusBar,
  WatermarkImage,
  WizardStepper,
} from "@/components/yaoqi";

export const metadata = {
  title: "曜齐 · 组件预览",
};

function Section({
  title,
  spec,
  children,
}: {
  title: string;
  spec: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3 rounded-lg border border-border bg-card/40 p-5">
      <header className="flex items-baseline justify-between">
        <h2 className="font-serif text-lg text-foreground">{title}</h2>
        <span className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          {spec}
        </span>
      </header>
      <div className="flex flex-wrap items-start gap-6 pt-2">{children}</div>
    </section>
  );
}

export default function ComponentsPreviewPage() {
  return (
    <div className="min-h-screen bg-background pb-24">
      <header className="border-b border-border bg-card/30">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-2 px-6 py-10">
          <BrandLogo size="lg" withTagline />
          <p className="text-sm text-muted-foreground">
            M1 Foundation · 组件预览页 ·{" "}
            <span className="text-[var(--color-gold-antique)]">仅内测可见</span>
          </p>
        </div>
      </header>

      <main className="mx-auto grid max-w-5xl gap-6 px-6 py-10">
        <Section title="1. BrandLogo" spec="UI-Spec §2.1">
          <BrandLogo size="sm" />
          <BrandLogo size="md" />
          <BrandLogo size="lg" withTagline />
        </Section>

        <Section title="2. MockBadge" spec="UI-Spec §3.2">
          <MockBadge status="real" />
          <MockBadge status="mock" />
          <MockBadge status="pending" />
          <MockBadge status="later" />
        </Section>

        <Section title="3. LockedCard" spec="UI-Spec §10.2">
          <div className="w-full max-w-md">
            <LockedCard />
          </div>
        </Section>

        <Section title="4. WatermarkImage" spec="UI-Spec §12.2">
          <div className="w-48">
            <WatermarkImage
              src="/mock/images/jadeite-bangle.svg"
              alt="翡翠手镯"
              caseNo="YQ-2026-0001"
              userSuffix="0001"
            />
          </div>
          <div className="w-48">
            <WatermarkImage
              src="/mock/images/hetian-pendant.svg"
              alt="和田玉吊坠"
              caseNo="YQ-2026-0002"
              userSuffix="0002"
              ratio="portrait"
            />
          </div>
        </Section>

        <Section title="5. DisclaimerNote" spec="UI-Spec §16">
          <div className="w-full max-w-md">
            <DisclaimerNote />
          </div>
          <DisclaimerNote variant="inline" />
        </Section>

        <Section title="6. StatusBar" spec="UI-Spec §15">
          <div className="w-full">
            <StatusBar
              items={[
                { key: "case", label: "案例", value: "已分析", status: "mock" },
                { key: "ocr", label: "OCR", value: "成功", status: "mock" },
                { key: "ai", label: "AI 报告", value: "Mock 报告", status: "mock" },
                { key: "oss", label: "图片 OSS", value: "本地占位", status: "pending" },
              ]}
            />
          </div>
        </Section>

        <Section title="7. WizardStepper" spec="UI-Spec §7">
          <div className="w-full">
            <WizardStepper current={2} />
          </div>
        </Section>

        <Section title="8. MobileBottomNav" spec="UI-Spec §4.1">
          <p className="text-sm text-muted-foreground">
            底部固定显示，仅在 ≤768px 视窗下显现。可缩小窗口或在 DevTools 中切换到 iPhone 模拟观察。
          </p>
        </Section>

        <Section title="9. shadcn/ui Button (主题验证)" spec="brand token mapping">
          <Button>默认 (古金)</Button>
          <Button variant="secondary">次要</Button>
          <Button variant="outline">边框</Button>
          <Button variant="ghost">幽灵</Button>
          <Button variant="destructive">危险</Button>
        </Section>
      </main>

      <MobileBottomNav />
    </div>
  );
}
