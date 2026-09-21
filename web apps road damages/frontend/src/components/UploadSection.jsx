import { useState, useRef, useCallback } from "react"

const ACCEPT_IMAGE = ".jpg,.jpeg,.png"
const ACCEPT_VIDEO = ".mp4,.mov,.mpeg"

export default function UploadSection({ fileType, file, preview, onFileSelect, onAnalyze, isLoading, errorMsg }) {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef(null)

  const handleDrop = useCallback((e) => {
    e.preventDefault(); setIsDragging(false)
    if (e.dataTransfer.files[0]) onFileSelect(e.dataTransfer.files[0])
  }, [onFileSelect])

  const isImage = fileType === "image"
  const accept = isImage ? ACCEPT_IMAGE : ACCEPT_VIDEO

  return (
    <div className="animate-fade-in-up space-y-6">
      <div
        onDrop={handleDrop} onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }} onDragLeave={() => setIsDragging(false)}
        className={`relative rounded-2xl border-2 border-dashed transition-all duration-200 cursor-pointer ${isDragging ? "dropzone-active" : ""}`}
        style={{
          borderColor: isDragging ? "#6366f1" : "var(--color-border)",
          background: isDragging ? "rgba(99,102,241,0.08)" : "var(--color-bg-card)",
          minHeight: "360px", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "2rem"
        }}
        onClick={() => !preview && inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" accept={accept} className="hidden" onChange={(e) => { if(e.target.files[0]) onFileSelect(e.target.files[0]) }} />
        {preview ? (
          <div className="w-full flex flex-col items-center gap-4 animate-fade-in">
            {isImage ? <img src={preview} alt="Preview" className="max-h-64 rounded-xl object-contain shadow-lg" /> 
                     : <video src={preview} className="max-h-64 rounded-xl shadow-lg" controls />}
            <p className="text-sm text-gray-400">{file?.name}</p>
            <button onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }} className="text-xs px-3 py-1.5 rounded-lg text-indigo-300 border border-indigo-500/30 bg-indigo-500/10">Change file</button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-indigo-500/10 border border-indigo-500/20">
              <span className="text-2xl">📥</span>
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-200 mb-1">Drag & drop {isImage ? "image" : "video"}</p>
              <p className="text-sm text-gray-500">or click to browse · max 50 MB</p>
            </div>
          </div>
        )}
      </div>

      {errorMsg && <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{errorMsg}</div>}

      <button
        onClick={onAnalyze} disabled={!file || isLoading}
        className="w-full py-4 rounded-xl text-base font-bold transition-all duration-200 flex items-center justify-center gap-3 disabled:opacity-40 disabled:cursor-not-allowed"
        style={file && !isLoading ? { background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff" } : { background: "var(--color-bg-surface)", color: "var(--color-text-muted)" }}
      >
        {isLoading ? "Running detection..." : "Run Detection"}
      </button>
    </div>
  )
}
