import QuoteCard from './QuoteCard'
import ScreenerCard from './ScreenerCard'
import NewsCard from './NewsCard'
import ComparisonCard from './ComparisonCard'
import RiskCard from './RiskCard'
import DCFCard from './DCFCard'
import CompsCard from './CompsCard'
import DuPontCard from './DuPontCard'
import WACCCard from './WACCCard'
import PortfolioCard from './PortfolioCard'
import BondCard from './BondCard'
import RatiosCard from './RatiosCard'
import ExcelExportCard from './ExcelExportCard'
import DataImportCard from './DataImportCard'

function parseTableRows(tableMd: string): Array<Record<string, any>> {
  const lines = tableMd.split('\n').filter(l => l.trim() && !l.includes('|---'))
  if (lines.length < 2) return []

  const headers = lines[0].split('|').map(h => h.trim()).filter(Boolean)
  return lines.slice(1).map(line => {
    const cells = line.split('|').map(c => c.trim()).filter(Boolean)
    const row: Record<string, any> = {}
    headers.forEach((h, i) => {
      const raw = cells[i]
      if (raw) {
        const num = parseFloat(raw.replace(/[₹,]/g, ''))
        row[h.toLowerCase().replace(/\s+/g, '_')] = isNaN(num) ? raw : num
      }
    })
    return row
  })
}

function extractSymbol(content: string): string | null {
  const match = content.match(/##\s*(?:Quote|quote)\s*(?:for|:)\s*(\w+)/)
  return match ? match[1] : null
}

function extractSymbols(content: string): string[] {
  const match = content.match(/##\s*(?:Comparison|Compare|comparing)\s*(.+)/i)
  if (match) {
    return match[1].split(/vs|and|,/).map(s => s.trim().toUpperCase()).filter(Boolean)
  }
  return []
}

function detectToolType(content: string): { type: 'quote' | 'screener' | 'news' | 'comparison' | 'risk' | null; symbol?: string; symbols?: string[]; data: any } {
  const firstHeading = content.match(/^##\s*(.+)/m)
  if (!firstHeading) return { type: null, data: null }

  const heading = firstHeading[1].toLowerCase()

  if (heading.includes('quote') || heading.includes('snapshot')) {
    const symbol = extractSymbol(content) || heading.replace(/.*quote\s*(?:for|:)?\s*/i, '').trim().split(/\s/)[0]
    const rows = parseTableRows(content)
    const data: Record<string, any> = { symbol }
    rows.forEach(row => Object.assign(data, row))
    return { type: 'quote', symbol, data }
  }

  if (heading.includes('screener') || heading.includes('screen result') || heading.includes('filter result')) {
    return { type: 'screener', data: parseTableRows(content) }
  }

  if (heading.includes('news') || heading.includes('headline')) {
    const articles: any[] = []
    const lines = content.split('\n')
    let current: any = {}
    for (const line of lines) {
      if (line.startsWith('- **') || line.startsWith('* **')) {
        if (current.headline) articles.push(current)
        current = { headline: line.replace(/^[-*]\s*\*\*(.+?)\*\*.*/, '$1') }
      } else if (line.includes('|')) {
        const parts = line.split('|').map(p => p.trim())
        parts.forEach(p => {
          if (p.toLowerCase().includes('source')) current.source = p.split(':')[1]?.trim()
          if (p.toLowerCase().includes('sentiment')) current.sentiment = p.split(':')[1]?.trim()
        })
      } else if (line.match(/\[.*\]/) && current.headline) {
        const urlMatch = line.match(/\((https?:\/\/[^)]+)\)/)
        if (urlMatch) current.url = urlMatch[1]
      }
    }
    if (current.headline) articles.push(current)
    if (!articles.length) {
      content.split(/\d+\.\s+/).slice(1).forEach(item => {
        const l = item.split('\n').filter(Boolean)
        if (l.length) articles.push({ headline: l[0].replace(/^[-*]\s*/, '').trim() })
      })
    }
    return { type: 'news', data: articles }
  }

  if (heading.includes('comparison') || heading.includes('compare') || heading.includes('vs ')) {
    return { type: 'comparison', symbols: extractSymbols(content), data: parseTableRows(content) }
  }

  if (heading.includes('risk') || heading.includes('var') || heading.includes('monte carlo') || heading.includes('stress test')) {
    const symbolMatch = content.match(/(?:for|:)?\s*([A-Z]{2,10})(?:\s|$)/)
    const data: Record<string, any> = {}
    for (const line of content.split('\n')) {
      const m = line.match(/\*\*([^*]+)\*\*\s*:\s*(.+)/)
      if (m) {
        const key = m[1].toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
        const val = parseFloat(m[2].replace(/[₹,%]/g, ''))
        data[key] = isNaN(val) ? m[2].trim() : val
      }
    }
    return { type: 'risk', symbol: symbolMatch?.[1] || '', data }
  }

  return { type: null, data: null }
}

interface ToolResultRendererProps {
  content: string
  role: 'user' | 'assistant'
  toolResults?: Record<string, any>
}

function renderCardsFromStructured(toolResults: Record<string, any>) {
  const cards: React.ReactNode[] = []

  for (const [tool, data] of Object.entries(toolResults)) {
    if (tool === 'get_quote' && data) {
      cards.push(<QuoteCard key="quote" symbol={data.symbol || 'N/A'} data={data} />)
    } else if (tool === 'run_screener' && Array.isArray(data)) {
      cards.push(<ScreenerCard key="screener" results={data} />)
    } else if (tool === 'search_news' && Array.isArray(data)) {
      cards.push(<NewsCard key="news" articles={data} />)
    } else if ((tool === 'compare_stocks' || tool === 'get_comparison') && Array.isArray(data)) {
      cards.push(<ComparisonCard key="compare" symbols={data.map((d: any) => d.symbol).filter(Boolean)} data={data} />)
    } else if ((tool === 'run_risk_analysis' || tool === 'run_monte_carlo') && data) {
      cards.push(<RiskCard key="risk" symbol={data.symbol || ''} data={data} />)
    } else if (tool === 'run_dcf_valuation' && data) {
      cards.push(<DCFCard key="dcf" data={data} />)
    } else if (tool === 'run_comps_analysis' && data) {
      cards.push(<CompsCard key="comps" data={data} />)
    } else if (tool === 'run_dupont_analysis' && data) {
      cards.push(<DuPontCard key="dupont" data={data} />)
    } else if (tool === 'calculate_wacc' && data) {
      cards.push(<WACCCard key="wacc" data={data} />)
    } else if (tool === 'run_portfolio_optimization' && data) {
      cards.push(<PortfolioCard key="portfolio" data={data} />)
    } else if (tool === 'calculate_bond_metrics' && data) {
      cards.push(<BondCard key="bond" data={data} />)
    } else if (tool === 'run_financial_ratio_analysis' && data) {
      cards.push(<RatiosCard key="ratios" data={data} />)
    } else if (tool === 'export_analysis_to_excel' && data) {
      cards.push(<ExcelExportCard key="excel" data={data} />)
    } else if (tool === 'import_financial_data' && data) {
      cards.push(<DataImportCard key="import" data={data} />)
    }
  }

  return cards.length > 0 ? cards : null
}

export default function ToolResultRenderer({ content, role, toolResults }: ToolResultRendererProps) {
  if (role !== 'assistant') return null

  if (toolResults && Object.keys(toolResults).length > 0) {
    const cards = renderCardsFromStructured(toolResults)
    if (cards) {
      return <div className="space-y-3 mb-3">{cards}</div>
    }
  }

  const detection = detectToolType(content)
  if (!detection.type) return null

  const card = (() => {
    switch (detection.type) {
      case 'quote':
        return <QuoteCard symbol={detection.symbol!} data={detection.data} />
      case 'screener':
        return detection.data.length > 0 ? <ScreenerCard results={detection.data} /> : null
      case 'news':
        return detection.data.length > 0 ? <NewsCard articles={detection.data} /> : null
      case 'comparison':
        return detection.data.length > 0 ? <ComparisonCard symbols={detection.symbols || []} data={detection.data} /> : null
      case 'risk':
        return <RiskCard symbol={detection.symbol || ''} data={detection.data} />
    }
  })()

  return card ? <div className="mb-3">{card}</div> : null
}
