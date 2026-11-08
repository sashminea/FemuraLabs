import type { Metadata } from "next";

import { Bento } from "@/components/marketing/bento";
import { CliTabs } from "@/components/marketing/cli-tabs";
import { Cta } from "@/components/marketing/cta";
import { Hero } from "@/components/marketing/hero";
import { Limits } from "@/components/marketing/limits";
import { Marquee } from "@/components/marketing/marquee";
import { Oss } from "@/components/marketing/oss";
import { Pipeline } from "@/components/marketing/pipeline";
import { Problem } from "@/components/marketing/problem";
import { Proof } from "@/components/marketing/proof";
import { Stats } from "@/components/marketing/stats";

export const metadata: Metadata = {
  title: { absolute: "FemuraLabs — Lower-limb CT analysis" },
};

export default function LandingPage() {
  return (
    <>
      <Hero />
      <Marquee />
      <Stats />
      <Problem />
      <Pipeline />
      <Bento />
      <Proof />
      <CliTabs />
      <Oss />
      <Limits />
      <Cta />
    </>
  );
}
