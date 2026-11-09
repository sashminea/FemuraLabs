const ITEMS = [
  "Python",
  "PyTorch",
  "MONAI",
  "SegResNet",
  "SimpleITK",
  "NumPy",
  "TotalSegmentator",
  "3D Slicer",
  "Typer",
  "Rich",
  "Docker",
  "pytest",
  "Kaggle",
];

export function Marquee() {
  const doubled = [...ITEMS, ...ITEMS];
  return (
    <div
      id="marquee"
      className="overflow-hidden border-b border-line py-5 [mask-image:linear-gradient(90deg,transparent,#000_12%,#000_88%,transparent)]"
    >
      <div className="flex w-max gap-14 animate-[marquee_40s_linear_infinite] hover:[animation-play-state:paused]">
        {doubled.map((item, i) => (
          <span
            key={`${item}-${i}`}
            className="whitespace-nowrap text-[clamp(1.1rem,2vw,1.5rem)] tracking-[-0.03em] text-dim"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
