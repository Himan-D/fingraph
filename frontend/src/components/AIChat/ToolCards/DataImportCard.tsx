import { FileSpreadsheet, FileText } from 'lucide-react'

interface DataImportCardProps {
  data: Record<string, any>
}

export default function DataImportCard({ data }: DataImportCardProps) {
  if (!data) return null

  if (data.file_type === 'csv') {
    const preview = data.records?.slice(0, 10) || []
    return (
      <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
        <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-b border-terminal-border">
          <div className="p-2 bg-amber-500/20 rounded-lg">
            <FileText size={18} className="text-amber-400" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">Imported Data</h3>
            <p className="text-xs text-terminal-muted">CSV • {data.row_count} rows • {data.columns?.length} columns</p>
          </div>
        </div>
        <div className="overflow-x-auto max-h-60 overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-terminal-border sticky top-0 bg-terminal-card">
                {data.columns?.map((col: string) => (
                  <th key={col} className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.map((row: any, i: number) => (
                <tr key={i} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                  {data.columns.map((col: string) => (
                    <td key={col} className="p-2 text-xs font-mono">{row[col] != null ? String(row[col]) : '—'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.row_count > 10 && (
          <div className="p-2 text-center text-[10px] text-terminal-muted border-t border-terminal-border">
            Showing 10 of {data.row_count} rows
          </div>
        )}
      </div>
    )
  }

  const sheetNames = data.sheet_names || Object.keys(data.sheets || {})
  const firstSheet = sheetNames[0]
  const sheetData = data.sheets?.[firstSheet]

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-3 p-3 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-b border-terminal-border">
        <div className="p-2 bg-amber-500/20 rounded-lg">
          <FileSpreadsheet size={18} className="text-amber-400" />
        </div>
        <div>
          <h3 className="font-semibold text-sm">Imported Data</h3>
          <p className="text-xs text-terminal-muted">
            {data.file_type?.toUpperCase()} • {sheetNames.length} sheet(s)
          </p>
        </div>
      </div>

      {sheetData && (
        <div className="overflow-x-auto max-h-60 overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-terminal-border sticky top-0 bg-terminal-card">
                {sheetData.headers?.map((h: string) => (
                  <th key={h} className="text-left p-2 text-[10px] uppercase text-terminal-muted font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sheetData.data?.slice(0, 10).map((row: any, i: number) => (
                <tr key={i} className="border-b border-terminal-border/50 hover:bg-terminal-bg/50 transition-colors">
                  {sheetData.headers.map((h: string) => (
                    <td key={h} className="p-2 text-xs font-mono">{row[h] != null ? String(row[h]) : '—'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sheetData?.row_count > 10 && (
        <div className="p-2 text-center text-[10px] text-terminal-muted border-t border-terminal-border">
          Showing 10 of {sheetData.row_count} rows in "{firstSheet}"
        </div>
      )}

      {sheetNames.length > 1 && (
        <div className="flex gap-1.5 p-2 border-t border-terminal-border flex-wrap">
          {sheetNames.map((s: string) => (
            <span key={s} className="px-2 py-0.5 bg-terminal-bg border border-terminal-border rounded text-[10px] text-terminal-muted">
              {s} ({data.sheets?.[s]?.row_count || 0} rows)
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
