export default function LoadingOverlay({ mode }) {
  return (
    <div id="loading-overlay" className="flex flex-col items-center justify-center py-20 gap-8 animate-fade-in">
      {/* Animated ring */}
      <div className="relative w-24 h-24">
        <div
          className="absolute inset-0 rounded-full animate-spin-slow"
          style={{ border: "3px solid transparent", borderTopColor: "#6366f1", borderRightColor: "#8b5cf6" }}
        />
        <div
          className="absolute inset-3 rounded-full flex items-center justify-center"
          style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="1.8">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </div>
      </div>

      {/* Text */}
      <div className="text-center space-y-2">
        <p className="text-lg font-semibold" style={{ color: "var(--color-text-primary)" }}>
          Running Detection...
        </p>
        <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
          {mode === "video"
            ? "Processing video frame-by-frame with ByteTrack. This may take a moment."
            : "Analyzing image with YOLO object detection."}
        </p>
      </div>

      {/* Progress steps */}
      <div className="space-y-3 w-full max-w-sm">
        {[
          { label: "Loading model inference", done: true },
          { label: mode === "video" ? "Tracking objects across frames" : "Detecting damage regions", done: true },
          { label: "Drawing bounding boxes & labels", done: false },
        ].map(({ label, done }, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: done ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.05)", border: `1px solid ${done ? "rgba(99,102,241,0.4)" : "rgba(255,255,255,0.1)"}` }}>
              {done ? (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              ) : (
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
              )}
            </div>
            <span className="text-sm" style={{ color: done ? "var(--color-text-secondary)" : "var(--color-text-muted)" }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
