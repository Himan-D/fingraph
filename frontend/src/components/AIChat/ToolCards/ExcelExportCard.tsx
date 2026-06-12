import { FileSpreadsheet, Download, Table, FolderOpen } from 'lucide-react'

interface ExcelExportCardProps {
  data: Record<string, any>
}

function downloadBase64File(base64: string, fileName: string) {
  const byteCharacters = atob(base64)
  const byteNumbers = new Array(byteCharacters.length)
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i)
  }
  const byteArray = new Uint8Array(byteNumbers)
  const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()
  URL.revokeObjectURL(url)
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function ExcelExportCard({ data }: ExcelExportCardProps) {
  const { file_name, file_size_bytes, sheets, content_base64 } = data
  if (!file_name) return null

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-b border-terminal-border">
        <div className="p-2 bg-green-500/20 rounded-lg">
          <FileSpreadsheet size={18} className="text-green-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Excel Export</h3>
          <p className="text-xs text-terminal-muted">{data.symbol} • {data.analysis_type}</p>
        </div>
      </div>

      <div className="p-3 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Table size={14} className="text-terminal-muted" />
            <span className="text-sm font-medium">{file_name}</span>
          </div>
          <span className="text-xs text-terminal-muted">{formatFileSize(file_size_bytes)}</span>
        </div>

        {sheets && sheets.length > 0 && (
          <div className="flex items-center gap-2">
            <FolderOpen size={14} className="text-terminal-muted" />
            <div className="flex gap-1.5 flex-wrap">
              {sheets.map((s: string) => (
                <span key={s} className="px-2 py-0.5 bg-terminal-bg border border-terminal-border rounded text-[10px] text-terminal-muted">
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}

        {content_base64 && (
          <button
            onClick={() => downloadBase64File(content_base64, file_name)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/90 transition-colors"
          >
            <Download size={16} />
            Download Excel
          </button>
        )}
      </div>
    </div>
  )
}
