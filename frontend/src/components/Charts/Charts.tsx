import { useState, useEffect, useRef, useCallback } from 'react'
import { createChart, IChartApi, ISeriesApi, CandlestickData, LineData, HistogramData, Time } from 'lightweight-charts'
import axios from 'axios'
import {
  LineChart, CandlestickChart, BarChart3, TrendingUp, 
  ZoomIn, ZoomOut, RotateCcw, Maximize2, Minimize2,
  Plus, X, ChevronDown, ArrowUpRight, ArrowDownRight
} from 'lucide-react'

interface ChartData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

interface IndicatorData {
  time: string
  value: number
}

const TIMEFRAMES = [
  { label: '1D', days: 1 },
  { label: '1W', days: 7 },
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
  { label: 'ALL', days: 0 },
]

const CHART_TYPES = [
  { id: 'candlestick', name: 'Candles', icon: CandlestickChart },
  { id: 'line', name: 'Line', icon: LineChart },
  { id: 'area', name: 'Area', icon: TrendingUp },
  { id: 'bar', name: 'Bar', icon: BarChart3 },
]

const INDICATORS = [
  { id: 'sma20', name: 'SMA 20', type: 'overlay', color: '#ffa500' },
  { id: 'sma50', name: 'SMA 50', type: 'overlay', color: '#00ffff' },
  { id: 'ema20', name: 'EMA 20', type: 'overlay', color: '#ff69b4' },
  { id: 'bb', name: 'Bollinger', type: 'overlay', color: '#888888' },
  { id: 'rsi', name: 'RSI (14)', type: 'separate', color: '#ff6b6b', upper: 70, lower: 30 },
  { id: 'macd', name: 'MACD', type: 'separate', color: '#4ecdc4' },
]

function calculateSMA(data: ChartData[], period: number): IndicatorData[] {
  const result: IndicatorData[] = []
  for (let i = period - 1; i < data.length; i++) {
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    result.push({ time: data[i].time, value: sum / period })
  }
  return result
}

function calculateEMA(data: ChartData[], period: number): IndicatorData[] {
  const result: IndicatorData[] = []
  const multiplier = 2 / (period + 1)
  let ema = data.slice(0, period).reduce((sum, d) => sum + d.close, 0) / period
  
  for (let i = period - 1; i < data.length; i++) {
    if (i === period - 1) {
      result.push({ time: data[i].time, value: ema })
    } else {
      ema = (data[i].close - ema) * multiplier + ema
      result.push({ time: data[i].time, value: ema })
    }
  }
  return result
}

function calculateBollingerBands(data: ChartData[], period: number = 20, stdDev: number = 2): { upper: IndicatorData[], middle: IndicatorData[], lower: IndicatorData[] } {
  const sma = calculateSMA(data, period)
  const upper: IndicatorData[] = []
  const lower: IndicatorData[] = []
  
  for (let i = period - 1; i < data.length; i++) {
    const slice = data.slice(i - period + 1, i + 1)
    const mean = sma[i - period + 1]?.value || slice.reduce((s, d) => s + d.close, 0) / period
    const variance = slice.reduce((s, d) => s + Math.pow(d.close - mean, 2), 0) / period
    const std = Math.sqrt(variance)
    
    upper.push({ time: data[i].time, value: mean + stdDev * std })
    lower.push({ time: data[i].time, value: mean - stdDev * std })
  }
  
  return { upper, middle: sma, lower }
}

export default function Charts() {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  
  const candlestickSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null)
  const lineSeriesRef = useRef<ISeriesApi<"Line"> | null>(null)
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null)
  const barSeriesRef = useRef<ISeriesApi<"Bar"> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null)
  const sma20Ref = useRef<ISeriesApi<"Line"> | null>(null)
  const sma50Ref = useRef<ISeriesApi<"Line"> | null>(null)
  const ema20Ref = useRef<ISeriesApi<"Line"> | null>(null)
  const bbUpperRef = useRef<ISeriesApi<"Line"> | null>(null)
  const bbLowerRef = useRef<ISeriesApi<"Line"> | null>(null)
  const bbMiddleRef = useRef<ISeriesApi<"Line"> | null>(null)
  
  const [symbol, setSymbol] = useState(() => new URLSearchParams(window.location.search).get('symbol') || 'RELIANCE')
  const [symbolInput, setSymbolInput] = useState(symbol)
  const [loading, setLoading] = useState(true)
  const [chartType, setChartType] = useState<'candlestick' | 'line' | 'area' | 'bar'>('candlestick')
  const [timeframe, setTimeframe] = useState('1Y')
  const [error, setError] = useState<string | null>(null)
  const [allData, setAllData] = useState<ChartData[]>([])
  const [chartReady, setChartReady] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const [activeIndicators, setActiveIndicators] = useState<string[]>(['volume'])
  const [showIndicatorMenu, setShowIndicatorMenu] = useState(false)
  const [crosshairData, setCrosshairData] = useState<{time: string, open: number, high: number, low: number, close: number, volume?: number} | null>(null)
  const [quote, setQuote] = useState<any>(null)
  const [darkMode] = useState(true)
  
  const chartColors = darkMode ? {
    bg: '#0d1117',
    text: '#8b949e',
    grid: '#21262d',
    border: '#30363d',
    success: '#3fb950',
    danger: '#f85149',
    accent: '#58a6ff',
  } : {
    bg: '#ffffff',
    text: '#24292f',
    grid: '#e1e4e8',
    border: '#d0d7de',
    success: '#1a7f37',
    danger: '#cf222e',
    accent: '#0969da',
  }

  const initChart = useCallback(() => {
    if (!chartContainerRef.current) return

    if (chartRef.current) {
      chartRef.current.remove()
      chartRef.current = null
    }

    chartRef.current = createChart(chartContainerRef.current, {
      layout: {
        background: { color: chartColors.bg },
        textColor: chartColors.text,
      },
      grid: {
        vertLines: { color: chartColors.grid },
        horzLines: { color: chartColors.grid },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: chartColors.accent, labelBackgroundColor: chartColors.accent },
        horzLine: { color: chartColors.accent, labelBackgroundColor: chartColors.accent },
      },
      rightPriceScale: {
        borderColor: chartColors.border,
        scaleMargins: { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor: chartColors.border,
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { vertTouchDrag: false },
    })

    candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
      upColor: chartColors.success,
      downColor: chartColors.danger,
      borderUpColor: chartColors.success,
      borderDownColor: chartColors.danger,
      wickUpColor: chartColors.success,
      wickDownColor: chartColors.danger,
    })

    lineSeriesRef.current = chartRef.current.addLineSeries({
      color: chartColors.accent,
      lineWidth: 2,
    })

    areaSeriesRef.current = chartRef.current.addAreaSeries({
      lineColor: chartColors.accent,
      topColor: `${chartColors.accent}40`,
      bottomColor: `${chartColors.accent}00`,
    })

    barSeriesRef.current = chartRef.current.addBarSeries({
      upColor: chartColors.success,
      downColor: chartColors.danger,
    })

    volumeSeriesRef.current = chartRef.current.addHistogramSeries({
      color: `${chartColors.accent}80`,
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    })
    volumeSeriesRef.current.priceScale().applyOptions({ scaleMargins: { top: 0.85, bottom: 0 } })

    sma20Ref.current = chartRef.current.addLineSeries({ color: '#ffa500', lineWidth: 1 })
    sma50Ref.current = chartRef.current.addLineSeries({ color: '#00ffff', lineWidth: 1 })
    ema20Ref.current = chartRef.current.addLineSeries({ color: '#ff69b4', lineWidth: 1 })
    bbUpperRef.current = chartRef.current.addLineSeries({ color: '#888888', lineWidth: 1, lineStyle: 2 })
    bbMiddleRef.current = chartRef.current.addLineSeries({ color: '#888888', lineWidth: 1 })
    bbLowerRef.current = chartRef.current.addLineSeries({ color: '#888888', lineWidth: 1, lineStyle: 2 })

    chartRef.current.subscribeCrosshairMove((param) => {
      if (param.time && param.seriesData.size > 0) {
        const candleData = param.seriesData.get(candlestickSeriesRef.current!) as CandlestickData
        if (candleData) {
          setCrosshairData({
            time: String(candleData.time),
            open: candleData.open,
            high: candleData.high,
            low: candleData.low,
            close: candleData.close,
          })
        }
      }
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

    setChartReady(true)
    return () => window.removeEventListener('resize', handleResize)
  }, [chartColors])

  useEffect(() => {
    initChart()
  }, [initChart])

  useEffect(() => {
    if (chartReady && symbol) {
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
        const seen = new Set()
        const data = response.data.data
          .map((d: any) => ({
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
    if (!data.length || !chartRef.current) return

    const sortedData = [...data].sort((a, b) => a.time.localeCompare(b.time))
    const timeframeDays = TIMEFRAMES.find(t => t.label === timeframe)?.days || 365
    const filteredData = timeframeDays > 0 ? sortedData.slice(-timeframeDays) : sortedData

    candlestickSeriesRef.current?.setData(filteredData as CandlestickData<Time>[])
    lineSeriesRef.current?.setData(filteredData.map(d => ({ time: d.time as Time, value: d.close })) as LineData<Time>[])
    areaSeriesRef.current?.setData(filteredData.map(d => ({ time: d.time as Time, value: d.close })) as any)
    barSeriesRef.current?.setData(filteredData.map(d => ({ 
      time: d.time as Time, 
      open: d.open, 
      high: d.high, 
      low: d.low, 
      close: d.close 
    })) as any)

    volumeSeriesRef.current?.setData(filteredData.map(d => ({
      time: d.time as Time,
      value: d.volume || 0,
      color: d.close >= d.open ? `${chartColors.success}60` : `${chartColors.danger}60`,
    })) as HistogramData<Time>[])

    // Indicators
    if (activeIndicators.includes('sma20')) {
      sma20Ref.current?.setData(calculateSMA(data, 20).map(d => ({ time: d.time as Time, value: d.value })) as LineData<Time>[])
    }
    if (activeIndicators.includes('sma50')) {
      sma50Ref.current?.setData(calculateSMA(data, 50).map(d => ({ time: d.time as Time, value: d.value })) as LineData<Time>[])
    }
    if (activeIndicators.includes('ema20')) {
      ema20Ref.current?.setData(calculateEMA(data, 20).map(d => ({ time: d.time as Time, value: d.value })) as LineData<Time>[])
    }
    if (activeIndicators.includes('bb')) {
      const bb = calculateBollingerBands(data, 20, 2)
      bbUpperRef.current?.setData(bb.upper.map(d => ({ time: d.time as Time, value: d.value })) as LineData<Time>[])
      bbMiddleRef.current?.setData(bb.middle.map(d => ({ time: d.time as Time, value: d.value })) as LineData<Time>[])
      bbLowerRef.current?.setData(bb.lower.map(d => ({ time: d.time as Time, value: d.value })) as LineData<Time>[])
    }

    // Toggle visibility
    candlestickSeriesRef.current?.applyOptions({ visible: chartType === 'candlestick' })
    lineSeriesRef.current?.applyOptions({ visible: chartType === 'line' })
    areaSeriesRef.current?.applyOptions({ visible: chartType === 'area' })
    barSeriesRef.current?.applyOptions({ visible: chartType === 'bar' })
    sma20Ref.current?.applyOptions({ visible: activeIndicators.includes('sma20') })
    sma50Ref.current?.applyOptions({ visible: activeIndicators.includes('sma50') })
    ema20Ref.current?.applyOptions({ visible: activeIndicators.includes('ema20') })
    bbUpperRef.current?.applyOptions({ visible: activeIndicators.includes('bb') })
    bbMiddleRef.current?.applyOptions({ visible: activeIndicators.includes('bb') })
    bbLowerRef.current?.applyOptions({ visible: activeIndicators.includes('bb') })

    chartRef.current.timeScale().fitContent()
  }

  useEffect(() => {
    if (chartReady && allData.length) {
      updateChart(allData)
    }
  }, [timeframe, chartType, activeIndicators, chartReady, allData])

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

  const toggleIndicator = (id: string) => {
    setActiveIndicators(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const handleZoomIn = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().scrollToPosition(5, false)
    }
  }

  const handleZoomOut = () => {
    if (chartRef.current) {
      chartRef.current.timeScale().scrollToPosition(-5, false)
    }
  }

  const handleReset = () => {
    chartRef.current?.timeScale().fitContent()
  }

  const toggleFullscreen = () => {
    setFullscreen(prev => !prev)
  }

  const pctChange = crosshairData ? ((crosshairData.close - crosshairData.open) / crosshairData.open) * 100 : (quote?.pct_change || 0)
  const displayData = crosshairData || quote || {}

  return (
    <div className={`${fullscreen ? 'fixed inset-0 z-50' : 'flex flex-col h-full'} bg-[${chartColors.bg}]`}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b" style={{ borderColor: chartColors.border, backgroundColor: chartColors.bg }}>
        <div className="flex items-center gap-3">
          <form onSubmit={handleSearch} className="flex items-center gap-2">
            <input
              type="text"
              value={symbolInput}
              onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
              placeholder="Symbol"
              className="w-24 px-3 py-1.5 rounded-lg text-sm font-mono"
              style={{ backgroundColor: chartColors.bg, border: `1px solid ${chartColors.border}`, color: chartColors.text }}
            />
            <button type="submit" className="px-3 py-1.5 rounded-lg text-sm font-medium text-white" style={{ backgroundColor: chartColors.accent }}>
              Go
            </button>
          </form>
          
          {/* Chart Type */}
          <div className="flex items-center gap-1 rounded-lg p-1" style={{ backgroundColor: chartColors.grid }}>
            {CHART_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => setChartType(type.id as any)}
                className="p-1.5 rounded flex items-center gap-1 text-xs font-medium transition-colors"
                style={{
                  backgroundColor: chartType === type.id ? chartColors.accent : 'transparent',
                  color: chartType === type.id ? 'white' : chartColors.text
                }}
                title={type.name}
              >
                <type.icon size={16} />
              </button>
            ))}
          </div>

          {/* Timeframe */}
          <div className="flex items-center gap-1 rounded-lg p-1" style={{ backgroundColor: chartColors.grid }}>
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf.label}
                onClick={() => setTimeframe(tf.label)}
                className="px-2 py-1 rounded text-xs font-medium transition-colors"
                style={{
                  backgroundColor: timeframe === tf.label ? chartColors.accent : 'transparent',
                  color: timeframe === tf.label ? 'white' : chartColors.text
                }}
              >
                {tf.label}
              </button>
            ))}
          </div>

          {/* Indicators */}
          <div className="relative">
            <button
              onClick={() => setShowIndicatorMenu(!showIndicatorMenu)}
              className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium"
              style={{ backgroundColor: chartColors.grid, color: chartColors.text }}
            >
              <Plus size={14} />
              Indicators
              <ChevronDown size={12} />
            </button>
            {showIndicatorMenu && (
              <div className="absolute top-full left-0 mt-1 rounded-lg shadow-xl z-10 min-w-[160px]" style={{ backgroundColor: chartColors.bg, border: `1px solid ${chartColors.border}` }}>
                {INDICATORS.filter(i => i.type === 'overlay').map((ind) => (
                  <button
                    key={ind.id}
                    onClick={() => toggleIndicator(ind.id)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:opacity-80"
                    style={{ color: chartColors.text }}
                  >
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: ind.color }} />
                    <span>{ind.name}</span>
                    {activeIndicators.includes(ind.id) && <span className="ml-auto">✓</span>}
                  </button>
                ))}
                <div className="border-t my-1" style={{ borderColor: chartColors.border }} />
                <button
                  onClick={() => toggleIndicator('volume')}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs hover:opacity-80"
                  style={{ color: chartColors.text }}
                >
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: chartColors.accent }} />
                  <span>Volume</span>
                  {activeIndicators.includes('volume') && <span className="ml-auto">✓</span>}
                </button>
              </div>
            )}
          </div>

          {/* Active indicators badges */}
          <div className="flex items-center gap-1">
            {activeIndicators.filter(i => i !== 'volume').map(id => {
              const ind = INDICATORS.find(i => i.id === id)
              return ind ? (
                <span
                  key={id}
                  className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium"
                  style={{ backgroundColor: `${ind.color}30`, color: ind.color }}
                >
                  {ind.name}
                  <X size={10} className="cursor-pointer" onClick={() => toggleIndicator(id)} />
                </span>
              ) : null
            })}
          </div>
        </div>

        {/* Price & Controls */}
        <div className="flex items-center gap-4">
          <div>
            <div className="text-xl font-bold font-mono" style={{ color: chartColors.text }}>{symbol}</div>
            {quote?.name && <div className="text-xs" style={{ color: chartColors.text }}>{quote.name}</div>}
          </div>
          
          <div className="h-8 w-px" style={{ backgroundColor: chartColors.border }} />
          
          <div>
            <div className="text-2xl font-bold font-mono" style={{ color: chartColors.text }}>
              ₹{(displayData.price || displayData.close || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div className="flex items-center gap-1 text-sm font-mono" style={{ color: pctChange >= 0 ? chartColors.success : chartColors.danger }}>
              {pctChange >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {pctChange >= 0 ? '+' : ''}{pctChange.toFixed(2)}%
            </div>
          </div>

          {crosshairData && (
            <>
              <div className="h-8 w-px" style={{ backgroundColor: chartColors.border }} />
              <div className="grid grid-cols-4 gap-3 text-xs font-mono">
                <div><span style={{ color: chartColors.text }}>O</span> <span>{crosshairData.open.toFixed(2)}</span></div>
                <div><span style={{ color: chartColors.success }}>H</span> <span>{crosshairData.high.toFixed(2)}</span></div>
                <div><span style={{ color: chartColors.danger }}>L</span> <span>{crosshairData.low.toFixed(2)}</span></div>
                <div><span style={{ color: chartColors.text }}>C</span> <span>{crosshairData.close.toFixed(2)}</span></div>
              </div>
            </>
          )}

          <div className="h-8 w-px" style={{ backgroundColor: chartColors.border }} />

          <div className="flex items-center gap-1">
            <button onClick={handleZoomIn} className="p-1.5 rounded hover:opacity-80" style={{ color: chartColors.text }} title="Zoom In"><ZoomIn size={16} /></button>
            <button onClick={handleZoomOut} className="p-1.5 rounded hover:opacity-80" style={{ color: chartColors.text }} title="Zoom Out"><ZoomOut size={16} /></button>
            <button onClick={handleReset} className="p-1.5 rounded hover:opacity-80" style={{ color: chartColors.text }} title="Reset"><RotateCcw size={16} /></button>
            <button onClick={toggleFullscreen} className="p-1.5 rounded hover:opacity-80" style={{ color: chartColors.text }} title={fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
              {fullscreen ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 relative" style={{ minHeight: fullscreen ? 'calc(100vh - 120px)' : '400px' }}>
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ backgroundColor: chartColors.bg }}>
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-t-transparent" style={{ borderColor: chartColors.accent }} />
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center z-10" style={{ backgroundColor: chartColors.bg }}>
            <div className="text-center">
              <div className="mb-2" style={{ color: chartColors.danger }}>{error}</div>
              <button onClick={fetchAllData} className="px-4 py-2 rounded-lg text-white" style={{ backgroundColor: chartColors.accent }}>Retry</button>
            </div>
          </div>
        )}
        <div ref={chartContainerRef} className="w-full h-full" />
      </div>

      {/* Footer Stats */}
      <div className="flex items-center gap-6 p-3 border-t" style={{ borderColor: chartColors.border, backgroundColor: chartColors.bg }}>
        {quote && (
          <>
            <div><span className="text-[10px]" style={{ color: chartColors.text }}>O</span> <span className="text-xs font-mono ml-1">{quote.open?.toFixed(2)}</span></div>
            <div><span className="text-[10px]" style={{ color: chartColors.success }}>H</span> <span className="text-xs font-mono ml-1">{quote.high?.toFixed(2)}</span></div>
            <div><span className="text-[10px]" style={{ color: chartColors.danger }}>L</span> <span className="text-xs font-mono ml-1">{quote.low?.toFixed(2)}</span></div>
            <div><span className="text-[10px]" style={{ color: chartColors.text }}>C</span> <span className="text-xs font-mono ml-1">{quote.price?.toFixed(2)}</span></div>
            <div className="h-4 w-px" style={{ backgroundColor: chartColors.border }} />
            <div><span className="text-[10px]" style={{ color: chartColors.text }}>Vol</span> <span className="text-xs font-mono ml-1">{((quote.volume || 0) / 1000000).toFixed(1)}M</span></div>
            <div className="h-4 w-px" style={{ backgroundColor: chartColors.border }} />
            <div><span className="text-[10px]" style={{ color: chartColors.text }}>Mkt Cap</span> <span className="text-xs font-mono ml-1">{(quote.market_cap / 1000000000).toFixed(1)}B</span></div>
            <div className="h-4 w-px" style={{ backgroundColor: chartColors.border }} />
            <div><span className="text-[10px]" style={{ color: chartColors.text }}>P/E</span> <span className="text-xs font-mono ml-1">{quote.pe_ratio || 'N/A'}</span></div>
            <div className="h-4 w-px" style={{ backgroundColor: chartColors.border }} />
            <div><span className="text-[10px]" style={{ color: chartColors.success }}>52W H</span> <span className="text-xs font-mono ml-1">{quote.week52_high?.toFixed(2)}</span></div>
            <div><span className="text-[10px]" style={{ color: chartColors.danger }}>52W L</span> <span className="text-xs font-mono ml-1">{quote.week52_low?.toFixed(2)}</span></div>
          </>
        )}
      </div>
    </div>
  )
}
