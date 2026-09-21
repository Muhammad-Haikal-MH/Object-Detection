export default function Header() {
  return (
    <header className="w-full border-b" style={{ borderColor: "var(--color-border)", background: "rgba(7,7,15,0.9)", backdropFilter: "blur(20px)" }}>
      <div className="max-w-5xl mx-auto px-4 py-6 flex flex-col md:flex-row items-start md:items-center gap-4">
        {/* Logo + Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 17l3-6 3 3 4-8 4 8 3-3" />
              <path d="M3 20h18" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold leading-tight" style={{ color: "var(--color-text-primary)" }}>
              Road Damage <span className="gradient-text">Detector</span>
            </h1>
            <p className="text-xs font-medium" style={{ color: "var(--color-text-muted)" }}>AI Object Detection · Portfolio Project</p>
          </div>
        </div>

        {/* Separator on desktop */}
        <div className="hidden md:block flex-1" />

        {/* Model badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold" style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.25)", color: "#a5b4fc" }}>
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block animate-pulse" />
          YOLO · mAP50 = 81%
        </div>
      </div>

      {/* Hero band */}
      <div className="max-w-5xl mx-auto px-4 pb-8 pt-2">
        <p className="text-base leading-relaxed max-w-3xl" style={{ color: "var(--color-text-secondary)" }}>
          An AI-powered road damage detection system trained to identify{" "}
          <span className="font-semibold" style={{ color: "#f87171" }}>potholes</span> and{" "}
          <span className="font-semibold" style={{ color: "#facc15" }}>cracks</span> on Indonesian roads.
          Upload a photo or short video to get instant bounding-box predictions from the deployed YOLO model.
          Built as a final portfolio project — model selected after comparing bounding-box vs. segmentation approaches.
        </p>
      </div>
    </header>
  )
}
