export default function ResultsSection({ results, fileType, onReset }) {
  const isImage = fileType === "image"

  const potholeCount = isImage ? (results.pothole_count || 0) : (results.unique_pothole_count ?? results.pothole_count ?? 0)
  const crackCount = isImage ? (results.crack_count || 0) : (results.unique_crack_count ?? results.crack_count ?? 0)
  const total = potholeCount + crackCount

  return (
    <div className="animate-fade-in-up space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold" style={{ color: "var(--color-text-primary)" }}>Detection Results</h2>
        <button onClick={onReset} className="px-4 py-2 rounded-lg text-sm border border-gray-700 bg-gray-800/50 hover:bg-gray-800 transition-colors">Try Another</button>
      </div>

      <div className="flex flex-col xl:flex-row gap-6">
        <div className="flex-1 rounded-2xl overflow-hidden border border-gray-800 bg-gray-900">
          <div className="px-4 py-3 border-b border-gray-800 text-sm font-semibold text-gray-400">
            {isImage ? "📷 Annotated Image" : "🎬 Annotated Video"}
          </div>
          <div className="p-4 flex items-center justify-center min-h-[300px] bg-black">
            {isImage ? (
              <img src={`data:image/jpeg;base64,${results.image_base64}`} alt="Result" className="max-w-full rounded-xl max-h-[500px] object-contain" />
            ) : (
              <video src={results.videoUrl} controls className="max-w-full rounded-xl max-h-[500px]" />
            )}
          </div>
          {!isImage && (
            <div className="px-4 pb-4 mt-2">
              <a href={results.videoUrl} download="annotated.mp4" className="block text-center w-full py-2.5 rounded-lg text-sm text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors">
                Download Annotated Video
              </a>
            </div>
          )}
        </div>

        <div className="w-full xl:w-72 space-y-4">
          <div className="rounded-2xl p-5 border border-gray-800 bg-gray-900/50 space-y-4">
            <p className="text-sm font-semibold uppercase text-gray-500">
              {isImage ? "Damage Count" : "Unique Damage Count"}
            </p>
            
            <div className="flex items-center gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center text-lg">🕳️</div>
              <div>
                <p className="text-xs text-red-300">Pothole</p>
                <p className="text-2xl font-black text-red-500">{potholeCount}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
              <div className="w-10 h-10 rounded-xl bg-yellow-500/20 flex items-center justify-center text-lg">⚡</div>
              <div>
                <p className="text-xs text-yellow-300">Crack</p>
                <p className="text-2xl font-black text-yellow-500">{crackCount}</p>
              </div>
            </div>

            <div className="flex items-center justify-between px-2 pt-2 border-t border-gray-800">
              <span className="text-sm text-gray-400">Total</span>
              <span className="text-xl font-bold gradient-text">{total}</span>
            </div>

            {!isImage && (results.frames_processed || results.video_duration_seconds) && (
              <div className="pt-3 border-t border-gray-800/80 space-y-2 text-xs text-gray-400">
                {results.frames_processed && (
                  <div className="flex justify-between">
                    <span>Processed Frames:</span>
                    <span className="font-semibold text-gray-300">{results.frames_processed}</span>
                  </div>
                )}
                {results.video_duration_seconds && (
                  <div className="flex justify-between">
                    <span>Duration:</span>
                    <span className="font-semibold text-gray-300">{results.video_duration_seconds}s</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
