"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Term from "./Term";
import type { GlossaryKey } from "./glossary";
import { fmt } from "@/lib/format";

type Target = "neutral" | "valgus3" | "valgus6";

type Props = {
  preHka: number;
  preMpta: number;
  theta: number;
  gap: number;
  mpta: number;
  hka: number;
  target: Target;
  tMin: number;
  tMax: number;
  status: "under" | "target" | "over";
  widthMm: number;
  caseName: string;
  side: "R" | "L";
};

function interpolate(text: string, p: Props): string {
  return text.replace(/\{(\w+)\}/g, (_, key) => {
    switch (key) {
      case "hka": return `${fmt(p.hka, 2, true)}°`;
      case "preHka": return `${fmt(p.preHka, 2, true)}°`;
      case "mpta": return `${fmt(p.mpta)}°`;
      case "preMpta": return `${fmt(p.preMpta)}°`;
      case "theta": return `${p.theta.toFixed(1)}°`;
      case "gap": return `${p.gap.toFixed(2)} mm`;
      case "widthMm": return `${p.widthMm.toFixed(1)} mm`;
      case "tMin": return `${fmt(p.tMin, 0)}°`;
      case "tMax": return `${fmt(p.tMax, 0, true)}°`;
      case "caseName": return p.caseName;
      case "side": return p.side === "R" ? "right" : "left";
      case "requiredTheta":
        return p.target === "neutral"
          ? `${p.preHka.toFixed(1)}°`
          : p.target === "valgus3"
          ? `${(p.preHka + 3).toFixed(1)}°`
          : `${(p.preHka + 6).toFixed(1)}°`;
      default: return "";
    }
  });
}

type Token =
  | { kind: "char"; value: string }
  | { kind: "term"; value: string; alias: string | null };

function tokenize(text: string): Token[] {
  const tokens: Token[] = [];
  const re = /\[\[([a-z_]+)(?:\|([^\]]+))?\]\]/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    for (let i = last; i < m.index; i++) tokens.push({ kind: "char", value: text[i] });
    tokens.push({ kind: "term", value: m[1], alias: m[2] ?? null });
    last = re.lastIndex;
  }
  for (let i = last; i < text.length; i++) tokens.push({ kind: "char", value: text[i] });
  return tokens;
}
/**
 * Streams the text in once per topic or variant. When only the numbers inside the
 * text change (slider drag), the text updates in place instead of restarting.
 */
function useStreamedTokens(tokens: Token[], streamKey: string) {
  const [count, setCount] = useState(0);
  const [thinking, setThinking] = useState(true);
  const [done, setDone] = useState(false);
  const tokensRef = useRef(tokens);
  tokensRef.current = tokens;

  useEffect(() => {
    setCount(0);
    setDone(false);
    setThinking(true);
    const perChar = Math.max(5, Math.min(18, 3000 / Math.max(tokensRef.current.length, 1)));
    let i = 0;
    let intervalId: ReturnType<typeof setInterval> | null = null;
    const t1 = setTimeout(() => {
      setThinking(false);
      intervalId = setInterval(() => {
        i++;
        setCount(i);
        if (i >= tokensRef.current.length) {
          if (intervalId) clearInterval(intervalId);
          setDone(true);
        }
      }, perChar);
    }, 340);
    return () => {
      clearTimeout(t1);
      if (intervalId) clearInterval(intervalId);
    };
  }, [streamKey]);

  return {
    shown: done ? tokens : tokens.slice(0, count),
    thinking,
    streaming: !done && count > 0,
  };
}

function renderTokens(tokens: Token[]): React.ReactNode {
  return tokens.map((t, i) =>
    t.kind === "term" ? (
      <Term key={i} term={t.value as GlossaryKey}>
        {t.alias || undefined}
      </Term>
    ) : (
      <span key={i}>{t.value}</span>
    )
  );
}

type Topic = {
  id: string;
  label: string;
  relevance: (p: Props) => number;
  variants: string[];
};

const TOPICS: Topic[] = [
  { id: "hka", label: "What is HKA?", relevance: () => 9, variants: [
    "The [[hka|HKA]] is the hip-knee-ankle angle. It measures the angle between the femoral axis (hip to knee) and the tibial axis (knee to ankle). Zero degrees means a straight leg. Positive is [[varus]], negative is [[valgus]]. Yours is currently {hka}.",
    "[[hka|HKA]] stands for hip-knee-ankle. It is the single number most surgeons watch during an alignment evaluation. It looks at whether the mechanical line from hip through knee to ankle bends inward or outward. Yours: {hka}.",
    "Think of [[hka|HKA]] as the angle that describes how the leg bends at the knee. It is measured in the [[coronalPlane|coronal plane]], the same plane you see in an AP X-ray. Normal is around 0. You are at {hka}.",
    "[[hka|HKA]] combines the femur direction and the tibia direction into one signed number. A straight lower limb has HKA of exactly zero. Anything else describes the residual bow or knock at the knee. Currently {hka}.",
  ]},
  { id: "mpta", label: "What is MPTA?", relevance: () => 8, variants: [
    "The [[mpta|MPTA]] is the medial proximal tibial angle. It measures the tilt of the tibial plateau against the tibial shaft. Normal range is about 85 to 90 degrees. Yours: {mpta}.",
    "[[mpta|MPTA]] describes how the joint line of the tibia sits relative to the shin bone's axis. Medial opening wedges raise it by exactly the wedge angle. That is why adding {theta} to the pre-op value yields {mpta}.",
    "The MPTA ([[mpta|medial proximal tibial angle]]) is a joint-line angle, not a whole-leg angle. It captures the geometry of the tibia only. Currently {mpta}, pre-op {preMpta}.",
    "[[mpta|MPTA]] is measured between the tibial axis and the [[jointLine|joint line]]. Every degree of medial opening wedge adds one degree to MPTA. Your value is {mpta}, derived from {preMpta} pre-op plus {theta} of correction.",
  ]},
  { id: "mldfa", label: "What is mLDFA?", relevance: () => 3, variants: [
    "[[mldfa|mLDFA]] is the femoral-side analogue of MPTA. Same idea, but on the thigh bone. Normal 85 to 90 degrees. Not affected by a tibial osteotomy because the cut is below the joint line.",
    "The mechanical lateral distal femoral angle ([[mldfa|mLDFA]]) describes how the distal femur sits relative to the femoral axis. Useful for describing overall alignment, but unchanged by an HTO.",
    "[[mldfa|mLDFA]] belongs to the femur, MPTA to the tibia. Both are joint-line angles. An HTO only changes MPTA.",
    "Think of [[mldfa|mLDFA]] as MPTA for the thigh. Since we are only opening the tibia in this simulator, mLDFA stays the same.",
  ]},
  { id: "hinge", label: "Lateral hinge", relevance: (p) => (p.theta > 0 ? 9 : 4), variants: [
    "The [[hinge]] is the intact lateral bridge of bone. The surgeon stops the cut just short of the outer cortex, so the distal tibia pivots around this point like a door on a hinge.",
    "Medial opening wedges rotate around a lateral [[hinge]]. The hinge is what keeps the bone connected. Its position determines the wedge geometry.",
    "The [[hinge]] is a small bridge of cortical bone left intact on the lateral side. Every degree you open at the medial side rotates the tibia around that bridge.",
    "Picture a book: the spine stays put, the pages open. In an HTO, the [[hinge]] is the spine.",
  ]},
  { id: "correction_angle", label: "Picking the angle", relevance: () => 7, variants: [
    "The [[correctionAngle]] is chosen to hit a target alignment. In practice surgeons usually aim for 3 to 6 degrees of valgus post-operatively. Small wedges (<10 degrees) heal reliably; larger ones need [[boneGraft]].",
    "Choosing the [[correctionAngle]] is a trade-off. Too small and the medial cartilage keeps wearing. Too large and the load shifts to the lateral compartment. Trying to hit {tMin} to {tMax} requires roughly {requiredTheta}.",
    "The correction angle depends on the preoperative deformity and the target. From your current {preHka} pre-op, reaching {tMin} to {tMax} means about {requiredTheta} of correction.",
    "Surgeons pick the [[correctionAngle]] based on the mechanical axis, patient age, weight, and cartilage status. Reaching a neutral target from {preHka} pre-op needs {requiredTheta} of correction.",
  ]},
  { id: "target_neutral", label: "Why neutral target?", relevance: (p) => (p.target === "neutral" ? 9 : 2), variants: [
    "A neutral target brings HKA to zero. It eliminates the varus deformity completely but does not overshoot into valgus.",
    "Choosing neutral means you want the leg perfectly straight. HKA of 0. Corrects the deformity without overloading the lateral side.",
    "Neutral target: HKA = 0. The mechanical axis passes exactly through the knee centre.",
    "A neutral target is the safest baseline. No overcorrection, no lateral overload.",
  ]},
  { id: "target_valgus3", label: "Why valgus 3?", relevance: (p) => (p.target === "valgus3" ? 9 : 2), variants: [
    "Three degrees of valgus is a common target. The mechanical axis passes just lateral of the knee centre, shifting more load off the medial compartment.",
    "Valgus 3 is the classic HTO target in many textbooks. Extra margin against recurrence of medial overload.",
    "A 3-degree valgus target shifts load more effectively than neutral without going aggressive.",
    "Valgus 3° is often chosen for patients with more advanced medial disease.",
  ]},
  { id: "target_valgus6", label: "Why valgus 6?", relevance: (p) => (p.target === "valgus6" ? 9 : 2), variants: [
    "Six degrees of valgus is a strong correction. Used in heavier patients or significant medial disease.",
    "Valgus 6 pushes the mechanical axis clearly into the lateral compartment. Less medial pain, but long-term lateral overload risk.",
    "A 6-degree valgus target is aggressive. Reserved for severe medial disease with healthy lateral cartilage.",
    "Valgus 6° overcorrects meaningfully. Lateral cartilage wear can become the next problem.",
  ]},
  { id: "wedge_gap", label: "The wedge gap", relevance: (p) => (p.theta > 0 ? 8 : 5), variants: [
    "The [[wedgeGap]] is the triangular gap between the two cut surfaces at the medial edge. You are at {gap}. Formula: [[wedgeGap|g = w · tan θ]], with w = {widthMm}.",
    "Every degree of opening wedge increases the medial [[wedgeGap]] non-linearly. At {theta}, the gap is {gap}.",
    "The [[wedgeGap]] determines how much bone has to fill the gap. Under 10 mm, bone graft is often optional. Over 12 mm, graft is standard.",
    "The [[wedgeGap]] is what the surgeon physically opens on the medial side. Right now you have {gap} of space.",
  ]},
  { id: "nonlinear", label: "Why the gap grows fast", relevance: (p) => (p.theta > 4 ? 8 : 3), variants: [
    "The gap uses the tangent function, which is non-linear. Doubling the angle more than doubles the gap.",
    "Tan grows faster than the angle itself. That is why a small extra degree opens an unexpectedly large wedge. Your current: {gap} at {theta}.",
    "Because g = w · tan θ, small corrections add almost linearly, but larger ones accelerate.",
    "At 5 degrees, gap is ~8.7% of width. At 10 degrees, ~17.6%. At 15 degrees, ~26.8%. That is tan bending upward.",
  ]},
  { id: "large_wedge", label: "Large wedge risks", relevance: (p) => (p.gap > 10 ? 9 : 4), variants: [
    "Wedges over 12 to 15 mm are considered large. They need [[boneGraft]], take longer to heal, and carry elevated [[nonUnion]] risk. Yours: {gap}.",
    "A large wedge stresses the fixation plate and delays healing. Above 12 mm, most surgeons fill with graft. Current: {gap}.",
    "Large wedges are surgical decisions with real trade-offs: reliable correction, higher failure rates.",
    "Under 10 mm may heal without graft, 10-15 mm usually needs graft, above 15 mm careful planning.",
  ]},
  { id: "bone_graft", label: "Bone graft", relevance: (p) => (p.gap > 12 ? 8 : 3), variants: [
    "[[boneGraft]] is bone material packed into the wedge to encourage healing. Required above 10-12 mm. Yours: {gap}.",
    "Autograft (patient's own), allograft (donor), or synthetic. Each has different healing profiles.",
    "For a large wedge, graft acts as scaffolding. Cells migrate in and slowly replace the graft with new bone.",
    "Modern HTO practice often uses small wedges that heal without graft. Larger wedges (>12 mm) typically use graft.",
  ]},
  { id: "non_union", label: "Non-union risk", relevance: (p) => (p.theta > 10 ? 8 : 3), variants: [
    "[[nonUnion]] means the cut bone never fully heals. Risk rises with wedge size, smoking, and poor blood supply.",
    "Non-union is the failure mode every HTO surgeon tries to avoid. Keep the wedge small if possible.",
    "Reported non-union rate after HTO is around 1-3% in well-selected patients.",
    "If the wedge does not consolidate, revision surgery may be needed. Conservative correction helps.",
  ]},
  { id: "overcorrection", label: "Overcorrection", relevance: (p) => (p.status === "over" ? 9 : 3), variants: [
    "[[overcorrection]] means pushing alignment past the target. In HTO this loads the lateral compartment.",
    "You have crossed the target band. Overcorrected alignment risks lateral-sided pain and cartilage loss.",
    "The point of HTO is load transfer. Too much overshoots — medial relief, lateral stress.",
    "Overcorrection is not harmless. Lateral overload can lead to failure within 10-15 years.",
  ]},
  { id: "undercorrection", label: "Undercorrection", relevance: (p) => (p.status === "under" ? 9 : 3), variants: [
    "[[undercorrection]] means not opening enough. Medial compartment keeps bearing excess load.",
    "You have not reached the target. Undercorrected alignment usually results in persistent medial pain.",
    "Undercorrection is more common than overcorrection. Slight over is usually safer than slight under.",
    "If you stop short of target, the axis still passes through the worn side. Second procedure may be needed.",
  ]},
  { id: "surgery", label: "How HTO surgery works", relevance: () => 6, variants: [
    "In a medial opening-wedge [[osteotomy|HTO]], the surgeon cuts the upper tibia from the medial side, stops short of the lateral cortex, opens a wedge, and fixes with a plate.",
    "Cut below the joint line, ~15 mm down. Intact lateral bridge = hinge. Wedge opened medially.",
    "About 45 to 60 minutes. Bone graft packed if needed. Small metal plate holds the gap open.",
    "Modern HTO uses a special plate with locking screws. Sometimes removed, often left in place.",
  ]},
  { id: "recovery", label: "Recovery timeline", relevance: () => 4, variants: [
    "6-8 weeks crutches, partial weight-bearing. Full weight-bearing 8-12 weeks. Sport 6-9 months.",
    "The wedge fills with bone over 6-12 weeks. X-rays confirm progress.",
    "Early recovery is conservative: limited weight-bearing protects the healing wedge.",
    "Long-term, well-selected patients can delay knee replacement by 10+ years.",
  ]},
  { id: "not_modeled", label: "What's not modeled", relevance: () => 5, variants: [
    "This simulator does not model soft tissue, bone healing beyond the wedge heuristic, hardware, weight-bearing alignment, tibial slope, or CORA principle.",
    "Missing: ligaments, menisci, cartilage balance, hardware design, deformity location, post-op rehab.",
    "The simulator treats bones as rigid geometry. Real surgery considers soft-tissue tension and weight-bearing alignment.",
    "For a full surgical plan, the surgeon evaluates CORA, tibial slope, and pre-op knee balance.",
  ]},
  { id: "data", label: "Data source", relevance: () => 3, variants: [
    "This simulator uses {preHka} pre-op HKA and {preMpta} pre-op MPTA from hand-placed landmarks on a real 3D CT. The mesh is decimated from the CT segmentation.",
    "Real patient geometry. Every number is derived from an actual CT case.",
    "CT → segmentation → 3D mesh → decimate → slice at cut plane. Pre-op angles from the reference landmarks.",
    "The pipeline behind this simulator is open source. Every geometry from a real cadaveric CT.",
  ]},
  { id: "varus", label: "What is varus?", relevance: (p) => (p.hka > 3 ? 8 : 2), variants: [
    "[[varus]] is bow-legged alignment. Knee sits lateral of the hip-ankle line. Positive HKA.",
    "In [[varus]] knees, the medial compartment bears more load. This is the pattern HTO corrects.",
    "[[varus]] is the classic HTO indication. Loads the inner knee where OA starts.",
    "Opposite of varus is [[valgus]]. Varus = knees outward.",
  ]},
  { id: "valgus", label: "What is valgus?", relevance: (p) => (p.hka < -3 ? 8 : 2), variants: [
    "[[valgus]] is knock-kneed. Knee sits medial of the hip-ankle line. Negative HKA.",
    "In [[valgus]] knees, lateral compartment bears more. Not typically treated with HTO.",
    "[[valgus]] is the mirror of varus: knees inward, feet apart.",
    "Mild valgus (0 to -3°) can be normal. Significant valgus usually a femoral deformity.",
  ]},
  { id: "plateau_width", label: "Plateau width", relevance: () => 5, variants: [
    "The [[plateauWidth]] is the mediolateral width of the tibial plateau. Typical adult: 70-85 mm. Yours: {widthMm}.",
    "Wider tibias need larger wedges for the same correction.",
    "Plateau width determines how far the medial edge moves for a given angle. Yours: {widthMm}.",
    "Lever arm w measured at the cut plane, not the plateau surface.",
  ]},
  { id: "coronal_plane", label: "What's the coronal plane?", relevance: () => 2, variants: [
    "The [[coronalPlane]] divides the body into front and back halves. All mechanical angles here are measured in this plane.",
    "Coronal plane = the plane of an AP X-ray. Front-to-back offsets are ignored.",
    "Coronal alignment is what the surgeon sees on an AP long-leg radiograph.",
    "The coronal plane is the front-facing view. Alignment measurements default to it.",
  ]},
  { id: "cut_plane", label: "Cut plane placement", relevance: () => 4, variants: [
    "The [[cutPlane]] is where the surgeon cuts the tibia, typically 10-20 mm below the joint line. This simulator fixes it at 15 mm below the top.",
    "Cut level affects wedge geometry and healing. Higher cuts heal faster but risk joint penetration.",
    "The cut plane respects the tibial tuberosity and patellar tendon attachment.",
    "This simulator uses a fixed 15 mm cut. Real procedures choose based on anatomy and CORA.",
  ]},
  { id: "osteotomy", label: "What is an osteotomy?", relevance: () => 3, variants: [
    "An [[osteotomy]] is a surgical cut through bone. HTO = upper shinbone. DFO = lower thighbone.",
    "[[osteotomy]] = osteo (bone) + tome (cut). The general term for a bone-cutting procedure.",
    "HTO is the best-known lower-limb osteotomy. Others exist for different deformities.",
    "The word [[osteotomy]] just means a cut in bone. In the knee context, realigning via a cut.",
  ]},
  { id: "alignment_matters", label: "Why alignment matters", relevance: () => 5, variants: [
    "Knee OA starts in the medial compartment. Varus overloads it. Correcting alignment shifts load laterally.",
    "Alignment determines where load passes. Varus = medial, valgus = lateral, neutral = balanced.",
    "Well-selected HTO patients can delay knee replacement by 10+ years.",
    "Alignment is one of the few modifiable factors in knee OA. Cartilage cannot regrow, but load can be shifted.",
  ]},
  { id: "deformity_severity", label: "How severe is my deformity?", relevance: (p) => (Math.abs(p.preHka) > 4 ? 7 : 3), variants: [
    "Severity: under 2° normal, 2-5° mild, 5-10° moderate, over 10° severe. Your pre-op HKA is {preHka}.",
    "Surgeons use HKA to grade deformity. Above 5° varus usually warrants considering osteotomy.",
    "Deformity severity helps decide treatment. Your case: {preHka} pre-op.",
    "Severity scale is not absolute. Same angle in a 30-year-old vs a 70-year-old differs.",
  ]},
  { id: "femoral_axis", label: "Femoral mechanical axis", relevance: () => 3, variants: [
    "The [[femoralAxis]] connects the hip centre to the knee centre. Drawn in solid blue.",
    "The femoral mechanical axis is one half of the mechanical alignment equation.",
    "Real surgeons measure from femoral head centre to knee centre. Errors propagate into HKA.",
    "The femoral axis does not change during an HTO — only the tibial axis rotates.",
  ]},
  { id: "tibial_axis", label: "Tibial mechanical axis", relevance: () => 3, variants: [
    "The [[tibialAxis]] connects the knee centre to the ankle centre. Rotates during an HTO.",
    "Every degree of wedge opening rotates the [[tibialAxis]] laterally. HKA shifts by that amount.",
    "The [[tibialAxis]] is drawn in green. Watch it move as you drag the slider.",
    "In a standing patient, the tibial axis passes through the ankle centre.",
  ]},
  { id: "joint_line", label: "Joint line", relevance: () => 4, variants: [
    "The [[jointLine]] is where the tibia meets the femur. Drawn as a short green line.",
    "Joint line orientation determines MPTA. Medial wedge raises it medially, raising MPTA.",
    "A horizontal joint line is ideal. Oblique = varus, what MPTA captures.",
    "The joint line is on the proximal fragment. Only the tibial axis below rotates.",
  ]},
  { id: "case_specific", label: "About this case", relevance: () => 4, variants: [
    "This is {caseName}, a {side} tibia from a cadaveric CT. Pre-op HKA {preHka}, pre-op MPTA {preMpta}. Tibia width at the cut plane: {widthMm}. Bone mesh decimated to ~10,000 triangles.",
    "{caseName} ({side} tibia). Geometry derived from a real CT segmentation. Every measurement here starts from hand-placed landmarks on that volume.",
    "Case {caseName}, {side} side. Pre-op deformity: {preHka}. Tibia width at cut plane: {widthMm}. The 3D model is the actual CT; nothing here is estimated.",
    "{caseName} is one of the subjects in the FemuraLabs validation set. {side} leg, {preHka} pre-op HKA, {preMpta} pre-op MPTA. The tibia at the cut plane measures {widthMm}.",
  ]},
];

const LIVE_INITIAL: string[] = [
  "At the current setting (θ = 0) no wedge has been opened. The leg is at its pre-op alignment of {preHka}. Try moving the slider to see how the correction changes HKA, MPTA, and the wedge gap.",
  "Before any correction. The mechanical axis is at {preHka}. Move the slider to open a medial wedge and watch HKA move toward zero.",
  "Pre-op state. Leg sits at {preHka} HKA. Every degree of medial opening reduces that by one degree.",
  "Nothing has been opened yet. Starting alignment is {preHka}. A medial opening wedge shifts this toward valgus.",
  "Uncorrected baseline. HKA {preHka}, MPTA {preMpta}, wedge gap 0 mm. Drag the correction angle to see changes.",
];

const LIVE_UNDER: string[] = [
  "You are at {theta} of correction and HKA has moved to {hka}. Still short of the {tMin} to {tMax} target band. About {requiredTheta} of correction would land on target.",
  "Wedge gap is {gap} at {theta} — HKA {hka}, still under-corrected. Straighter than pre-op but not inside the target band.",
  "Partial correction. HKA sits at {hka}. Wedge size {gap} is in the range where graft becomes a consideration if you go further.",
  "The alignment has moved from {preHka} to {hka}, an improvement, but target is {tMin} to {tMax}. Continue opening.",
  "Not yet there. {hka} is outside {tMin} to {tMax}. The mechanical axis is closer to the knee centre but still medial.",
];

const LIVE_TARGET: string[] = [
  "In target. HKA is {hka}, inside the {tMin} to {tMax} band. Wedge gap {gap}, MPTA {mpta}.",
  "Target reached. From {preHka} pre-op, {theta} of correction now puts HKA at {hka}.",
  "You are inside the target range. Wedge gap {gap} sits within typical healing-range sizes.",
  "Good alignment. HKA {hka}, MPTA {mpta}. Both angles sit in a plausible postoperative range.",
  "Successful correction. HKA settled at {hka} with a {gap} wedge. Remaining variation is close to measurement noise.",
];

const LIVE_OVER: string[] = [
  "Overcorrected. HKA is {hka}, past the {tMin} to {tMax} band. Load now shifts to the lateral compartment. Reduce the angle.",
  "You have gone past target. HKA {hka} vs {tMin} to {tMax} wanted. MPTA {mpta} is looking quite oblique. Back off.",
  "Overshoot. The leg is now in more valgus than intended. Reduce the angle to roughly {requiredTheta} to land in range.",
  "Too much correction. HKA {hka} means the mechanical axis is now lateral to the knee centre.",
  "Past target. Overcorrection would push load to the healthy lateral side and stress it. Target is {tMin} to {tMax}.",
];

function livePool(state: "initial" | "under" | "target" | "over"): string[] {
  switch (state) {
    case "initial": return LIVE_INITIAL;
    case "under": return LIVE_UNDER;
    case "target": return LIVE_TARGET;
    case "over": return LIVE_OVER;
  }
}

function liveState(p: Props): "initial" | "under" | "target" | "over" {
  if (p.theta < 0.01) return "initial";
  return p.status;
}

function rankTopics(p: Props, excludeIds: string[]): Topic[] {
  return TOPICS.filter((t) => !excludeIds.includes(t.id))
    .map((t) => ({ t, score: t.relevance(p) + Math.random() * 2 }))
    .sort((a, b) => b.score - a.score)
    .map(({ t }) => t);
}
function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ flexShrink: 0, opacity: 0.6 }}>
      <path d="M9 6l6 6-6 6" />
    </svg>
  );
}

export default function Explainer(p: Props) {
  const [currentTopicId, setCurrentTopicId] = useState<string | null>(null);
  const [variantIdx, setVariantIdx] = useState<Record<string, number>>({});
  const [liveVariantIdx, setLiveVariantIdx] = useState<Record<string, number>>({});
  const [recentlyAsked, setRecentlyAsked] = useState<string[]>([]);
  const [chipIds, setChipIds] = useState<string[]>([]);
  const stateKey = liveState(p);

  useEffect(() => {
    if (currentTopicId) return;
    const pool = livePool(stateKey);
    const prev = liveVariantIdx[stateKey];
    let next = Math.floor(Math.random() * pool.length);
    if (next === prev && pool.length > 1) next = (next + 1) % pool.length;
    if (next !== prev) {
      setLiveVariantIdx((v) => ({ ...v, [stateKey]: next }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stateKey, currentTopicId]);

  useEffect(() => {
    if (currentTopicId) return;
    const ranked = rankTopics(p, recentlyAsked);
    setChipIds(ranked.slice(0, 3).map((t) => t.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recentlyAsked, stateKey, p.target, currentTopicId]);

  const rawText = useMemo(() => {
    if (currentTopicId === null) {
      const pool = livePool(stateKey);
      const idx = liveVariantIdx[stateKey] ?? 0;
      return pool[idx];
    }
    const topic = TOPICS.find((t) => t.id === currentTopicId);
    if (!topic) return "";
    const idx = variantIdx[currentTopicId] ?? 0;
    return topic.variants[idx];
  }, [currentTopicId, stateKey, liveVariantIdx, variantIdx]);

  const tokens = useMemo(() => tokenize(interpolate(rawText, p)), [rawText, p]);
  const { shown, thinking, streaming } = useStreamedTokens(tokens, `${currentTopicId ?? "live"}|${rawText}`);

  const handleChipClick = (id: string) => {
    setCurrentTopicId(id);
    setVariantIdx((v) => ({ ...v, [id]: Math.floor(Math.random() * 4) }));
    setRecentlyAsked((prev) => [...prev, id].slice(-4));
  };

  const handleLiveClick = () => {
    setCurrentTopicId(null);
    setChipIds(rankTopics(p, recentlyAsked).slice(0, 3).map((t) => t.id));
  };

  const handleMoreClick = () => {
    const exclude = [...recentlyAsked, ...chipIds];
    const ranked = rankTopics(p, exclude);
    setChipIds(ranked.slice(0, 3).map((t) => t.id));
  };

  const title = currentTopicId
    ? TOPICS.find((t) => t.id === currentTopicId)?.label ?? ""
    : "Live commentary";

  return (
    <div>
      <style>{`
        @keyframes expBlink { 0%,50% { opacity: 1; } 50.01%,100% { opacity: 0; } }
        @keyframes expDot { 0%,80%,100% { opacity: .3; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-2px); } }
      `}</style>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          minHeight: 24,
          marginBottom: 10,
        }}
      >
        <h2 style={{ margin: 0, fontSize: 13, fontWeight: 500, letterSpacing: "-.01em", color: "var(--color-tx)" }}>
          {title}
        </h2>
        {currentTopicId && (
          <button className="sim-link" onClick={handleLiveClick}>
            Back to live
          </button>
        )}
      </div>

      <div
        aria-live="polite"
        style={{
          minHeight: 132,
          fontSize: 14,
          lineHeight: 1.65,
          letterSpacing: "-.005em",
          color: "rgba(236,235,230,.88)",
        }}
      >
        {thinking ? (
          <span style={{ display: "inline-flex", gap: 4, alignItems: "center", height: 23 }}>
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  background: "rgba(77,163,255,.7)",
                  animation: `expDot 900ms ${i * 140}ms infinite ease-in-out`,
                }}
              />
            ))}
          </span>
        ) : (
          <>
            {renderTokens(shown)}
            {streaming && (
              <span
                aria-hidden
                style={{
                  display: "inline-block",
                  width: 2,
                  height: "1em",
                  background: "var(--color-blue)",
                  marginLeft: 2,
                  verticalAlign: "text-bottom",
                  animation: "expBlink 900ms steps(1,end) infinite",
                }}
              />
            )}
          </>
        )}
      </div>

      <div style={{ marginTop: 20 }}>
        <div style={{ fontSize: 12, color: "var(--color-dim)", marginBottom: 6 }}>Ask about</div>
        <div>
          {chipIds.map((id) => {
            const topic = TOPICS.find((t) => t.id === id);
            if (!topic) return null;
            return (
              <button key={id} className="sim-ask" onClick={() => handleChipClick(id)}>
                {topic.label}
                <Chevron />
              </button>
            );
          })}
          <button
            className="sim-ask"
            onClick={handleMoreClick}
            style={{ color: "var(--color-dim)", borderBottom: `1px solid var(--color-line)` }}
          >
            More topics
            <Chevron />
          </button>
        </div>
      </div>
    </div>
  );
}