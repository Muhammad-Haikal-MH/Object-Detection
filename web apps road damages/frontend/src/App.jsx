import { useState, useCallback } from "react"
import Header from "./components/Header"
import UploadSection from "./components/UploadSection"
import ResultsSection from "./components/ResultsSection"
import LoadingOverlay from "./components/LoadingOverlay"
import Footer from "./components/Footer"

const API_BASE = import.meta.env.VITE_API_URL || ""

export default function App() {
  const [fileType, setFileType] = useState("image") // "image" | "video"
  const [modelType, setModelType] = useState("bbox") // "bbox" | "segmentation"
  
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [appState, setAppState] = useState("idle") // idle | loading | results | error
  const [results, setResults] = useState(null)
  const [errorMsg, setErrorMsg] = useState("")

  const handleFileSelect = useCallback((selectedFile) => {
    setFile(selectedFile)
    setResults(null)
    setErrorMsg("")
    setAppState("idle")
    if (selectedFile) {
      setPreview(URL.createObjectURL(selectedFile))
    } else {
      setPreview(null)
    }
  }, [])

  const handleAnalyze = useCallback(async () => {
    if (!file) return
    setAppState("loading")
    setResults(null)
    setErrorMsg("")

    const formData = new FormData()
    formData.append("file", file)
    formData.append("model_type", modelType) // Send model type to backend

    try {
      if (fileType === "image") {
        const res = await fetch(`${API_BASE}/predict/image`, {
          method: "POST",
          body: formData,
        })
        if (!res.ok) throw new Error(`Server error ${res.status}`)
        const data = await res.json()
        setResults({ type: "image", ...data })
        setAppState("results")
      } else {
        const res = await fetch(`${API_BASE}/predict/video`, {
          method: "POST",
          body: formData,
        })
        if (!res.ok) throw new Error(`Server error ${res.status}`)
        const summaryHeader = res.headers.get("X-Detection-Summary") || ""
        const summary = {}
        summaryHeader.split(",").forEach((pair) => {
          const [k, v] = pair.split("=")
          if (k) summary[k.trim()] = isNaN(v) ? v : Number(v)
        })
        const blob = await res.blob()
        const videoUrl = URL.createObjectURL(blob)
        setResults({ type: "video", videoUrl, ...summary })
        setAppState("results")
      }
    } catch (err) {
      setErrorMsg(err.message || "Something went wrong.")
      setAppState("error")
    }
  }, [file, fileType, modelType])

  const handleReset = useCallback(() => {
    setFile(null)
    setPreview(null)
    setResults(null)
    setErrorMsg("")
    setAppState("idle")
  }, [])

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--color-bg-base)" }}>
      <Header />

      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-8 flex flex-col md:flex-row gap-8">
        
        {/* Sidebar */}
        <aside className="w-full md:w-64 flex-shrink-0 space-y-6">
          <div className="p-5 rounded-2xl space-y-5" style={{ background: "var(--color-bg-card)", border: "1px solid var(--color-border)" }}>
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--color-text-muted)" }}>Media Type</h3>
              <div className="flex bg-gray-900 rounded-lg p-1">
                {["image", "video"].map((m) => (
                  <button
                    key={m}
                    onClick={() => { setFileType(m); handleReset() }}
                    className={`flex-1 py-1.5 text-xs font-semibold rounded-md capitalize ${fileType === m ? 'bg-indigo-600 text-white shadow' : 'text-gray-400'}`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--color-text-muted)" }}>Model Architecture</h3>
              <div className="space-y-2">
                <label className="flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors hover:bg-gray-800" style={{ border: `1px solid ${modelType === 'bbox' ? '#6366f1' : 'var(--color-border)'}`, background: modelType === 'bbox' ? 'rgba(99,102,241,0.1)' : 'transparent' }}>
                  <input type="radio" name="modelType" checked={modelType === 'bbox'} onChange={() => setModelType('bbox')} className="mt-1" />
                  <div>
                    <p className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>Bounding Box</p>
                    <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>YOLOv8 Fast Inference. mAP50=81</p>
                  </div>
                </label>
                
                <label className="flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors hover:bg-gray-800" style={{ border: `1px solid ${modelType === 'segmentation' ? '#6366f1' : 'var(--color-border)'}`, background: modelType === 'segmentation' ? 'rgba(99,102,241,0.1)' : 'transparent' }}>
                  <input type="radio" name="modelType" checked={modelType === 'segmentation'} onChange={() => setModelType('segmentation')} className="mt-1" />
                  <div>
                    <p className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>Segmentation</p>
                    <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>Dual Model (Crack + Pothole masks)</p>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <section className="flex-1">
          {appState !== "results" && (
            <UploadSection
              fileType={fileType}
              file={file}
              preview={preview}
              onFileSelect={handleFileSelect}
              onAnalyze={handleAnalyze}
              isLoading={appState === "loading"}
              errorMsg={appState === "error" ? errorMsg : ""}
            />
          )}

          {appState === "loading" && <LoadingOverlay mode={fileType} />}

          {appState === "results" && results && (
            <ResultsSection
              results={results}
              fileType={fileType}
              onReset={handleReset}
            />
          )}
        </section>

      </main>
      <Footer />
    </div>
  )
}
