import { useState, useEffect, useRef } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, Time } from 'lightweight-charts'
import axios from 'axios'
import { TrendingUp, TrendingDown, Volume2, BarChart2, LineChart, CandlestickChart, Settings } from 'lucide-react'

interface ChartData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

export default function Charts() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null)
  
  const [symbol, setSymbol] = useState('RELIANCE')
  const [symbolInput, setSymbolInput] = useState('RELIANCE')
  const [chartData, setChartData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(false)
  const [chartType, setChartType] = useState<'candlestick' | 'line'>('candlestick')
  const [timeframe, setTimeframe] = useState('1Y')
  
  const [quote, setQuote] = useState<any>(null)

  useEffect(() => {
    if (chartContainerRef.current && !chartRef.current) {
      chartRef.current = createChart(chartContainerRef.current, {
        layout: {
          background: { color: '#0d1117' },
          textColor: '#8b949e',
        },
        grid: {
          vertLines: { color: '#21262d' },
          horzLines: { color: '#21262d' },
        },
        crosshair: {
          mode: 1,
        },
        rightPriceScale: {
          borderColor: '#30363d',
        },
        timeScale: {
          borderColor: '#30363d',
          timeVisible: true,
        },
      })

      candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
        upColor: '#3fb950',
        downColor: '#f85149',
        borderUpColor: '#3fb950',
        borderDownColor: '#f85149',
        wickUpColor: '#3fb950',
        wickDownColor: '#f85149',
      })

      volumeSeriesRef.current = chartRef.current.addHistogramSeries({
        color: '#58a6ff',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: '',
      })

      volumeSeriesRef.current.priceScale().applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      })

      const handleResize = () => {
        if (chartRef.current && chartContainerRef.current) {
          chartRef.current.applyOptions({
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
          })
        }
      }

      window.addEventListener('resize', handleResize)
      handleResize()

      return () => {
        window.removeEventListener('resize', handleResize)
        if (chartRef.current) {
          chartRef.current.remove()
          chartRef.current = null
        }
      }
    }
  }, [])

  useEffect(() => {
    fetchChartData()
    fetchQuote()
  }, [symbol, timeframe])

  const fetchChartData = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/quotes/historical/${symbol}`)
      if (response.data.success && response.data.data) {
        const data = response.data.data.map((d: any) => ({
          time: d.timestamp?.split('T')[0] as Time,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume,
        }))
        setChartData(data)
        
        if (candlestickSeriesRef.current) {
          candlestickSeriesRef.current.setData(data)
        }
        if (volumeSeriesRef.current) {
          volumeSeriesRef.current.setData(
            data.map(d => ({
              time: d.time,
              value: d.volume || 0,
              color: d.close >= d.open ? 'rgba(63, 185, 80, 0.5)' : 'rgba(248, 81, 73, 0.5)',
            }))
          )
        }
        
        if (chartRef.current) {
          chartRef.current.timeScale().fitContent()
        }
      }
    } catch (error) {
      console.error('Failed to fetch chart data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchQuote = async () => {
    try {
      const response = await axios.get(`/api/v1/quotes/${symbol}`)
      if (response.data.success) {
        setQuote(response.data.data)
      }
    } catch (error) {
      console.error('Failed to fetch quote:', error)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setSymbol(symbolInput.toUpperCase())
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-terminal-border bg-terminal-card">
        <div className="flex items-center gap-4">
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <input
              type="text"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
              placeholder="Symbol"
              className="w-24 px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm font-mono focus:border-terminal-accent"
            />
            <button type="submit" className="px-3 py-1.5 bg-terminal-accent text-white rounded-lg text-sm hover:opacity-90">
              Load
            </button>
          </form>
          
          <div className="flex items-center gap-2 bg-terminal-bg rounded-lg p-1">
            <button
              onClick={() => setChartType('candlestick')}
              className={`p-1.5 rounded ${chartType === 'candlestick' ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
            >
              <CandlestickChart size={18} />
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`p-1.5 rounded ${chartType === 'line' ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
            >
              <LineChart size={18} />
            </button>
          </div>
        </div>

        {quote && (
          <div className="flex items-center gap-4">
            <div>
              <div className="text-2xl font-bold font-mono">₹{(quote.price || 0).toFixed(2)}</div>
              <div className={`text-sm font-mono ${(quote.pct_change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                {(quote.change || 0) >= 0 ? '+' : ''}{(quote.change || 0).toFixed(2)} ({(quote.pct_change || 0).toFixed(2)}%)
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-terminal-bg/50 z-10">
            <div className="text-terminal-muted">Loading chart...</div>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>

      {/* Quick Stats */}
      {quote && (
        <div className="p-4 border-t border-terminal-border bg-terminal-card grid grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-terminal-muted mb-1">Open</div>
            <div className="font-mono">₹{(quote.open || 0).toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-terminal-muted mb-1">High</div>
            <div className="font-mono text-terminal-success">₹{(quote.high || 0).toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-terminal-muted mb-1">Low</div>
            <div className="font-mono text-terminal-danger">₹{(quote.low || 0).toFixed(2)}</div>
          </div>
          <div>
            <div className="text-xs text-terminal-muted mb-1">Volume</div>
            <div className="font-mono">{((quote.volume || 0) / 1000000).toFixed(1)}M</div>
          </div>
        </div>
      )}
    </div>
  )
}
