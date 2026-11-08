export type GlossaryKey =
  | "hka"
  | "mpta"
  | "mldfa"
  | "varus"
  | "valgus"
  | "wedgeGap"
  | "hinge"
  | "medialOpeningWedge"
  | "targetValgus"
  | "mechanicalAxis"
  | "coronalPlane"
  | "cutPlane"
  | "plateauWidth"
  | "femoralAxis"
  | "tibialAxis"
  | "jointLine"
  | "osteotomy"
  | "correctionAngle"
  | "overcorrection"
  | "undercorrection"
  | "boneGraft"
  | "nonUnion"
  | "varusDeformity"
  | "valgusDeformity"
  | "femur"
  | "tibiaProximal"
  | "tibiaDistal"
  | "femoralExtension"
  | "hkaArc"
  | "mptaArc"
  | "wedge"
  | "landmarks"
  | "targetRange";

export const GLOSSARY: Record<GlossaryKey, string> = {
  hka: "Hip-Knee-Ankle angle. The angle between the femoral mechanical axis (hip→knee) and the tibial mechanical axis (knee→ankle), measured in the coronal plane. A straight leg has HKA = 0°. Positive HKA = varus (bow-legged). Negative HKA = valgus (knock-kneed).",
  mpta: "Medial Proximal Tibial Angle. The angle between the tibial mechanical axis and the joint line of the tibial plateau, measured on the medial side. Normal is roughly 85–90°. A medial opening wedge increases MPTA by exactly the correction angle θ.",
  mldfa:
    "Mechanical Lateral Distal Femoral Angle. The femoral-side analogue of MPTA. Normal roughly 85–90°. Not affected by a high tibial osteotomy.",
  varus:
    "Bow-legged. The knee sits medial to the hip-ankle line, so the distal part of the leg tilts toward the body's midline. Positive HKA in this convention.",
  valgus:
    "Knock-kneed. The knee sits lateral to the hip-ankle line, so the distal part of the leg tilts away from the midline. Negative HKA in this convention.",
  wedgeGap:
    "The triangular space opened between the two cut surfaces of the tibia at the medial edge. Formula: g = w · tan θ, where w is the tibia width at the cut plane and θ the correction angle.",
  hinge:
    "The point on the lateral (outer) cortex of the tibia where bone stays intact during a medial opening-wedge osteotomy. The distal tibia pivots around this point. Its location determines the wedge geometry.",
  medialOpeningWedge:
    "A surgical technique where a triangular wedge of bone is opened on the medial side of the tibia, with the lateral side left as a hinge. Opening the wedge pushes the distal tibia outward, correcting varus.",
  targetValgus:
    "The postoperative alignment the surgeon aims for. Real-world targets range from neutral (0°) to mild (3°) or moderate (6°) valgus, depending on the patient, cartilage status, and surgeon preference.",
  mechanicalAxis:
    "An imaginary line through the centre of the hip joint and the centre of the ankle joint. When it passes through the centre of the knee, the leg is straight. Medial or lateral deviations = malalignment.",
  coronalPlane:
    "The plane dividing the body into front and back halves. HKA, MPTA, and mLDFA are defined by projecting the mechanical axes into this plane.",
  cutPlane:
    "The horizontal plane where the surgeon cuts the tibia. Usually 10–20 mm below the joint line. This simulator fixes it at 15 mm below the top of the tibia.",
  plateauWidth:
    "The mediolateral width of the tibial plateau. Typical adult: 70–85 mm. This is the lever arm w in the wedge-gap formula.",
  femoralAxis:
    "The line from the centre of the hip to the centre of the knee. Together with the tibial axis it defines the mechanical alignment of the leg.",
  tibialAxis:
    "The line from the centre of the knee to the centre of the ankle. In a medial opening-wedge osteotomy this line rotates laterally as the wedge opens.",
  jointLine:
    "The surface where the tibia meets the femur, approximated here by a straight line between the medial and lateral edges of the tibial plateau. The angle between joint line and tibial axis is MPTA.",
  osteotomy:
    "A surgical procedure where bone is cut and repositioned. In a high tibial osteotomy (HTO), the cut is in the upper shinbone. In a distal femoral osteotomy (DFO), it is in the lower thighbone.",
  correctionAngle:
    "The angle θ the wedge is opened by. Each degree of medial opening reduces varus by roughly one degree in the coronal plane. For an adult tibia of width 80 mm, 1° of correction opens a wedge of roughly 1.4 mm.",
  overcorrection:
    "Reducing the HKA past the intended target — for example pushing a neutral target into valgus by too much. Overcorrection can overload the lateral compartment of the knee, the opposite of the problem the surgery tries to solve.",
  undercorrection:
    "Not opening the wedge enough to reach the intended target. The medial compartment keeps bearing too much load, defeating the purpose of the osteotomy.",
  boneGraft:
    "Bone material (autograft, allograft, or synthetic substitute) packed into a wedge that is opened more than ~10–12 mm, to help the gap fill with bone during healing. Small wedges may heal without graft.",
  nonUnion:
    "Failure of a cut bone to heal. More common with large wedges (>12–14°), smoking, and poor blood supply. This is one reason surgeons prefer the smallest correction that reaches the target.",
  varusDeformity:
    "The medical term for a varus knee. Measured in degrees, typically via HKA. Mild varus is 2–5°, moderate 5–10°, severe over 10°.",
  valgusDeformity:
    "The medical term for a valgus knee. Same severity scale as varus, but negative by HKA convention.",
  femur:
    "The thigh bone. Runs from the hip joint down to the knee joint. In this simulator it is static and does not move during the correction.",
  tibiaProximal:
    "The upper portion of the shin bone, above the osteotomy cut. Contains the tibial plateau (the joint surface) and stays fixed while the wedge opens below it.",
  tibiaDistal:
    "The lower portion of the shin bone, below the osteotomy cut. It rotates outward around the lateral hinge as you open the medial wedge.",
  femoralExtension:
    "The dashed blue line that continues the femoral axis below the knee. It shows where the leg would go if the tibia followed the femur direction with no bend. The HKA angle is measured between this reference and the actual tibial axis.",
  hkaArc:
    "The orange arc in the 3D scene. Its sweep equals the current HKA — the angle between the femoral reference and the tibial axis. Watch it collapse to zero as you reach neutral.",
  mptaArc:
    "The blue arc between the tibial axis and the joint line. Its sweep equals the current MPTA. Grows by exactly the correction angle as the wedge opens.",
  wedge:
    "The translucent orange triangle at the cut. Its base is the medial edge of the cut surface, its apex is the lateral hinge. Its opening angle equals the correction angle θ.",
  landmarks:
    "The coloured spheres marking four key anatomical points: blue at the hip centre, yellow at the knee centre, blue at the ankle centre, green at the lateral hinge. Every number in the simulator is computed relative to these points.",
  targetRange:
    "The band of HKA values that counts as hitting the selected target: neutral is −1° to +1°, valgus 3° is −2° to −4°, valgus 6° is −5° to −7°. The green zone on the angle slider marks the correction angles that land inside this band.",
};

export type DisplayKind =
  | "bone"
  | "solid"
  | "dashed"
  | "arc"
  | "wedge"
  | "markers";

export const DISPLAY_ITEMS: {
  key: GlossaryKey;
  label: string;
  group: string;
  color: string;
  kind: DisplayKind;
}[] = [
  {
    key: "femur",
    label: "Femur",
    group: "Bones",
    color: "#d4c9b0",
    kind: "bone",
  },
  {
    key: "tibiaProximal",
    label: "Proximal tibia",
    group: "Bones",
    color: "#d4c9b0",
    kind: "bone",
  },
  {
    key: "tibiaDistal",
    label: "Distal tibia",
    group: "Bones",
    color: "#d4c9b0",
    kind: "bone",
  },
  {
    key: "femoralAxis",
    label: "Femoral axis",
    group: "Axes",
    color: "#4da3ff",
    kind: "solid",
  },
  {
    key: "femoralExtension",
    label: "Femoral reference",
    group: "Axes",
    color: "#4da3ff",
    kind: "dashed",
  },
  {
    key: "tibialAxis",
    label: "Tibial axis",
    group: "Axes",
    color: "#10b981",
    kind: "solid",
  },
  {
    key: "jointLine",
    label: "Joint line",
    group: "Axes",
    color: "#10b981",
    kind: "solid",
  },
  {
    key: "hkaArc",
    label: "HKA arc",
    group: "Angles",
    color: "#ffaa55",
    kind: "arc",
  },
  {
    key: "mptaArc",
    label: "MPTA arc",
    group: "Angles",
    color: "#4da3ff",
    kind: "arc",
  },
  {
    key: "wedge",
    label: "Wedge triangle",
    group: "Angles",
    color: "#ff7733",
    kind: "wedge",
  },
  {
    key: "landmarks",
    label: "Joint markers",
    group: "Markers",
    color: "#10b981",
    kind: "markers",
  },
];
