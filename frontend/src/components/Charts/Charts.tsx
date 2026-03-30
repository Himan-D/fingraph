import { useState, useEffect, useRef } from 'react'
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts'
import axios from 'axios'
import { LineChart, CandlestickChart, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react'

interface ChartData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

const TIMEFRAMES = [
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: 'ALL', days: 0 },
]

export default function Charts() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const lineSeriesRef = useRef<ISeriesApi<"Line"> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null)
  
  const [symbol, setSymbol] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('symbol') || 'RELIANCE'
  })
  const [symbolInput, setSymbolInput] = useState(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('symbol') || 'RELIANCE'
  })
  const [loading, setLoading] = useState(true)
  const [chartType, setChartType] = useState<'candlestick' | 'line'>('candlestick')
  const [timeframe, setTimeframe] = useState('1Y')
  const [error, setError] = useState<string | null>(null)
  const [allData, setAllData] = useState<ChartData[]>([])
  const [chartReady, setChartReady] = useState(false)
  
  const [quote, setQuote] = useState<{
    price?: number, 
    change?: number, 
    pct_change?: number, 
    open?: number, 
    high?: number, 
    low?: number, 
    volume?: number, 
    name?: string,
    week52_high?: number,
    week52_low?: number,
  } | null>(null)

  // Initialize chart
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
          secondsVisible: false,
        },
        handleScroll: true,
        handleScale: true,
      })

      candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
        upColor: '#3fb950',
        downColor: '#f85149',
        borderUpColor: '#3fb950',
        borderDownColor: '#f85149',
        wickUpColor: '#3fb950',
        wickDownColor: '#f85149',
      })

      lineSeriesRef.current = chartRef.current.addLineSeries({
        color: '#58a6ff',
        lineWidth: 2,
      })
      lineSeriesRef.current.applyOptions({ visible: false })

      volumeSeriesRef.current = chartRef.current.addHistogramSeries({
        color: '#58a6ff',
        priceFormat: {
          type: 'volume',
        },
        priceScaleId: '',
      })

      volumeSeriesRef.current.priceScale().applyOptions({
        scaleMargins: {
          top: 0.85,
          bottom: 0,
        },
      })

      setChartReady(true)

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

  // Fetch all data when symbol changes
  useEffect(() => {
    if (chartReady) {
      fetchAllData()
      fetchQuote()
    }
  }, [symbol, chartReady])

  const fetchAllData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`/api/v1/quotes/historical/${symbol}`)
      if (response.data.success && response.data.data) {
        // Sort by time and remove duplicates
        const seen = new Set()
        const data = response.data.data
          .map((d: {timestamp?: string, time?: string, open: number, high: number, low: number, close: number, volume?: number}) => ({
            time: (d.timestamp || d.time || '').split('T')[0],
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
            volume: d.volume,
          }))
          .filter((d: ChartData) => {
            if (seen.has(d.time)) return false
            seen.add(d.time)
            return true
          })
          .sort((a: ChartData, b: ChartData) => a.time.localeCompare(b.time))
        
        setAllData(data)
        updateChart(data)
      }
    } catch (error: any) {
      console.error('Failed to fetch chart data:', error)
      setError(error?.response?.data?.message || 'Failed to load chart data')
    } finally {
      setLoading(false)
    }
  }

  const updateChart = (data: ChartData[]) => {
    if (!data.length) return

    // Sort data by time ascending
    const sortedData = [...data].sort((a, b) => a.time.localeCompare(b.time))

    // Filter by timeframe
    const timeframeDays = TIMEFRAMES.find(t => t.label === timeframe)?.days || 365
    const filteredData = timeframeDays > 0 
      ? sortedData.slice(-timeframeDays) 
      : sortedData

    if (candlestickSeriesRef.current) {
      candlestickSeriesRef.current.setData(filteredData)
    }
    if (lineSeriesRef.current) {
      lineSeriesRef.current.setData(filteredData.map(d => ({
        time: d.time,
        value: d.close,
      })))
    }
    if (volumeSeriesRef.current) {
      volumeSeriesRef.current.setData(
        filteredData.map(d => ({
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

  // Update chart when timeframe or chart type changes
  useEffect(() => {
    if (chartReady && allData.length) {
      updateChart(allData)
      
      // Toggle series visibility
      if (candlestickSeriesRef.current) {
        candlestickSeriesRef.current.applyOptions({ visible: chartType === 'candlestick' })
      }
      if (lineSeriesRef.current) {
        lineSeriesRef.current.applyOptions({ visible: chartType === 'line' })
      }
    }
  }, [timeframe, chartType, allData, chartReady])

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
    const newSymbol = symbolInput.toUpperCase().trim()
    if (newSymbol) {
      setSymbol(newSymbol)
      window.history.pushState({}, '', `/charts?symbol=${newSymbol}`)
    }
  }

  const handleZoomIn = () => {
    if (chartRef.current) {
      const zoom = chartRef.current.timeScale().getVisibleLogicalRange()
      if (zoom) {
        chartRef.current.timeScale().setVisibleLogicalRange({
          from: zoom.from * 0.8,
          to: zoom.to * 0.8,
        })
      }
    }
  }

  const handleZoomOut = () => {
    if (chartRef.current) {
      const zoom = chartRef.current.timeScale().getVisibleLogicalRange()
      if (zoom) {
        chartRef.current.timeScale().setVisibleLogicalRange({
          from: zoom.from * 1.2,
          to: zoom.to * 1.2,
        })
      }
    }
  }

  const handleReset = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent()
    }
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
              className="w-28 px-3 py-1.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm font-mono focus:border-terminal-accent"
            />
            <button type="submit" className="px-4 py-1.5 bg-terminal-accent text-white rounded-lg text-sm hover:opacity-90">
              Search
            </button>
          </form>
          
          {/* Chart Type Toggle */}
          <div className="flex items-center gap-2 bg-terminal-bg rounded-lg p-1">
            <button
              onClick={() => setChartType('candlestick')}
              className={`p-1.5 rounded flex items-center gap-1 ${chartType === 'candlestick' ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
              title="Candlestick"
            >
              <CandlestickChart size={18} />
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`p-1.5 rounded flex items-center gap-1 ${chartType === 'line' ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
              title="Line Chart"
            >
              <LineChart size={18} />
            </button>
          </div>

          {/* Timeframe Selection */}
          <div className="flex items-center gap-1 bg-terminal-bg rounded-lg p-1">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.label}
                onClick={() => setTimeframe(tf.label)}
                className={`px-2 py-1 rounded text-xs font-medium ${timeframe === tf.label ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center gap-1">
            <button onClick={handleZoomIn} className="p-1.5 hover:bg-terminal-border rounded text-terminal-muted" title="Zoom In">
              <ZoomIn size={16} />
            </button>
            <button onClick={handleZoomOut} className="p-1.5 hover:bg-terminal-border rounded text-terminal-muted" title="Zoom Out">
              <ZoomOut size={16} />
            </button>
            <button onClick={handleReset} className="p-1.5 hover:bg-terminal-border rounded text-terminal-muted" title="Reset">
              <RotateCcw size={16} />
            </button>
          </div>
        </div>

        {/* Stock Info */}
        <div className="flex items-center gap-4">
          <div>
            <div className="text-xl font-bold">{symbol}</div>
            {quote?.name && <div className="text-xs text-terminal-muted">{quote.name}</div>}
          </div>
          {quote && (
            <>
              <div className="h-8 w-px bg-terminal-border"></div>
              <div>
                <div className="text-2xl font-bold font-mono">₹{(quote.price || 0).toFixed(2)}</div>
                <div className={`text-sm font-mono ${(quote.pct_change || 0) >= 0 ? 'text-terminal-success' : 'text-terminal-danger'}`}>
                  {(quote.change || 0) >= 0 ? '+' : ''}{(quote.change || 0).toFixed(2)} ({(quote.pct_change || 0) >= 0 ? '+' : ''}{(quote.pct_change || 0).toFixed(2)}%)
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#0d1117] z-10">
            <div className="text-[#8b949e]">Loading chart...</div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#0d1117] z-10">
            <div className="text-center">
              <div className="text-[#f85149] mb-2">{error}</div>
              <button onClick={fetchAllData} className="px-4 py-2 bg-[#58a6ff] text-white rounded">
                Retry
              </button>
            </div>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>

      {/* Stats Footer */}
      {quote && (
        <div className="p-4 border-t border-terminal-border bg-terminal-card">
          <div className="grid grid-cols-6 gap-4">
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
            <div>
              <div className="text-xs text-terminal-muted mb-1">52W High</div>
              <div className="font-mono text-terminal-success">₹{(quote.week52_high || 0).toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-terminal-muted mb-1">52W Low</div>
              <div className="font-mono text-terminal-danger">₹{(quote.week52_low || 0).toFixed(2)}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
