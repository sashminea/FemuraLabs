import { Reveal } from "@/components/ui/reveal";

const NODES = [
  { title: "CT volume", sub: "Real millimetres, LPS frame" },
  {
    title: "SegResNet",
    sub: "Femur, tibia, fibula, talus",
    badge: "0.922 CV Dice",
  },
  { title: "3D meshes", sub: "Watertight surfaces" },
  { title: "Landmarks", sub: "Hip, knee, ankle centres" },
  { title: "Angles", sub: "HKA, mLDFA, MPTA" },
];

export function Pipeline() {
  return (
    <section id="pipeline" className="py-24 md:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid items-center gap-12 md:grid-cols-[1.1fr_0.9fr] md:gap-16">
          <Reveal>
            <h2 className="max-w-[14ch] text-[clamp(2rem,4.8vw,3.8rem)] font-medium leading-[1.04] tracking-[-0.055em]">
              From CT volume to angles, one straight path.
            </h2>
          </Reveal>

          <Reveal delay={120}>
            <svg
              viewBox="0 0 220 420"
              role="img"
              aria-label="A femur and tibia: a scan sweep reveals the segmentation mask, then hip, knee and ankle landmarks and the mechanical axis appear"
              className="mx-auto w-full max-w-[240px] md:ml-auto md:mr-0"
            >
              <defs>
                <path
                  id="fe"
                  d="M96 62C90 50 92 30 108 24C126 18 142 32 136 50C134 58 126 62 120 66C112 76 110 100 112 160C112 185 126 196 128 210C130 226 114 232 100 230C84 228 80 214 88 200C100 188 102 170 100 140C98 110 100 80 96 62Z"
                />
                <path
                  id="ti"
                  d="M80 246C80 238 96 236 110 238C124 238 130 244 126 252C118 262 116 290 116 330C116 360 120 384 126 398L96 398C98 380 98 350 96 320C94 290 90 268 80 246Z"
                />
                <clipPath id="sc">
                  <rect
                    x="0"
                    y="0"
                    width="220"
                    height="420"
                    className="origin-top animate-[sweep_8s_ease-in-out_infinite]"
                  />
                </clipPath>
                <linearGradient id="mg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor="#4da3ff" stopOpacity="0.5" />
                  <stop offset="1" stopColor="#4da3ff" stopOpacity="0.15" />
                </linearGradient>
              </defs>

              <use href="#fe" fill="none" stroke="rgba(255,255,255,0.28)" strokeWidth="1.2" />
              <use
                href="#ti"
                transform="rotate(7 104 240)"
                fill="none"
                stroke="rgba(255,255,255,0.28)"
                strokeWidth="1.2"
              />

              <g clipPath="url(#sc)" className="animate-[markappear_8s_ease-in-out_infinite]">
                <use href="#fe" fill="url(#mg)" stroke="#4da3ff" strokeWidth="1.2" />
                <use
                  href="#ti"
                  transform="rotate(7 104 240)"
                  fill="url(#mg)"
                  stroke="#4da3ff"
                  strokeWidth="1.2"
                />
              </g>

              <line
                x1="0"
                x2="220"
                y1="0"
                y2="0"
                stroke="#4da3ff"
                strokeWidth="1"
                className="animate-[scanline_8s_ease-in-out_infinite]"
              />

              <path
                d="M122 42L91.4 391.6"
                fill="none"
                stroke="#4da3ff"
                strokeWidth="1.2"
                pathLength={1}
                strokeDasharray={1}
                className="animate-[axisdraw_8s_ease-in-out_infinite]"
              />

              <g
                fill="#0a0a0a"
                stroke="#ecebe6"
                strokeWidth="1.3"
                className="animate-[landmark_8s_ease-in-out_infinite]"
              >
                <circle cx="122" cy="42" r="6" />
                <circle cx="106" cy="222" r="5" />
                <circle cx="91.4" cy="391.6" r="5" />
              </g>

              <g
                fontFamily="ui-monospace, Menlo, monospace"
                fontSize="9"
                fill="rgba(236,235,230,0.5)"
                letterSpacing="1"
                className="animate-[landmark_8s_ease-in-out_infinite]"
              >
                <text x="140" y="28">HIP</text>
                <text x="128" y="226">KNEE</text>
                <text x="108" y="395">ANKLE</text>
              </g>
            </svg>
          </Reveal>
        </div>

        <div className="relative mt-16 grid gap-3.5 md:grid-cols-5">
          <div
            aria-hidden
            className="pointer-events-none absolute left-[5%] right-[5%] top-1/2 hidden h-px bg-line md:block"
          />
          {NODES.map((node, i) => (
            <Reveal key={node.title} delay={i * 100}>
              <div
                data-cursor="card"
                className="relative rounded-2xl border border-line bg-bg p-6 md:p-7"
                style={{
                  animation: "glow 3.5s ease-in-out infinite",
                  animationDelay: `${i * 0.5}s`,
                }}
              >
                <h3 className="mb-1.5 text-[1.05rem] font-medium tracking-[-0.03em]">
                  {node.title}
                </h3>
                <p className="text-[13.5px] text-mut">{node.sub}</p>
                {node.badge && (
                  <span className="mt-3 inline-block rounded-full border border-line2 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.08em] text-mut">
                    {node.badge}
                  </span>
                )}
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
