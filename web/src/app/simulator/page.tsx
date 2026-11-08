import type { Metadata } from "next";
import SimulatorClient from "./SimulatorClient";

export const metadata: Metadata = {
  title: "Osteotomy Wedge Simulator | FemuraLabs",
  description:
    "Interactive geometric demonstration of a high tibial osteotomy: wedge gap, new MPTA, new HKA, computed from the medial opening-wedge formula g = w · tan θ.",
};

export default function Page() {
  return <SimulatorClient />;
}
