import { useState, useEffect } from 'react'
import axios from 'axios'
import { Clock, ExternalLink, Search, RefreshCw } from 'lucide-react'

interface NewsArticle {
  id: number
  headline: string
  summary: string
  source: string
  url: string
  published_at: string
  sentiment: string
  category: string
}

const CATEGORIES = [
  { id: 'all', name: 'All', color: 'bg-gray-500' },
  { id: 'bullish', name: 'Bullish', color: 'bg-green-500' },
  { id: 'bearish', name: 'Bearish', color: 'bg-red-500' },
  { id: 'neutral', name: 'Neutral', color: 'bg-blue-500' },
]

export default function News() {
  const [news, setNews] = useState<NewsArticle[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')

  useEffect(() => {
    fetchNews()
  }, [])

  const fetchNews = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/v1/news?limit=50`)
      if (response.data.success) {
        setNews(response.data.data || [])
      }
    } catch (error) {
      console.error('Failed to fetch news:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredNews = news.filter(item => {
    const matchesSearch = !searchQuery || 
      item.headline.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.source.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || item.sentiment === selectedCategory
    return matchesSearch && matchesCategory
  })

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (hours >= 24) return `${Math.floor(hours / 24)}d ago`
    if (hours >= 1) return `${hours}h ago`
    if (minutes >= 1) return `${minutes}m ago`
    return 'Just now'
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'text-green-400 bg-green-500/20'
      case 'bearish': return 'text-red-400 bg-red-500/20'
      case 'positive': return 'text-green-400 bg-green-500/20'
      case 'negative': return 'text-red-400 bg-red-500/20'
      default: return 'text-blue-400 bg-blue-500/20'
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-[#30363d] bg-[#161b22]">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📰</span>
          <h2 className="text-xl font-bold">Market News</h2>
          <span className="text-sm text-gray-400">({filteredNews.length} articles)</span>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search news..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64 pl-9 pr-4 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <button
            onClick={fetchNews}
            className="p-2 bg-[#21262d] hover:bg-[#30363d] rounded-lg transition-colors"
          >
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 p-4 border-b border-[#30363d] bg-[#161b22]/50">
        <span className="text-sm text-gray-400">Sentiment:</span>
        <div className="flex gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                selectedCategory === cat.id
                  ? `${cat.color} text-white`
                  : 'bg-[#21262d] text-gray-400 hover:bg-[#30363d]'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>
      </div>

      {/* News List */}
      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
          </div>
        ) : filteredNews.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400">
            <span className="text-4xl mb-4">📰</span>
            <p>No news articles found</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredNews.map((article) => (
              <div
                key={article.id}
                className="bg-[#161b22] border border-[#30363d] rounded-xl p-4 hover:border-[#58a6ff] transition-colors cursor-pointer group"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${getSentimentColor(article.sentiment)}`}>
                        {article.sentiment || 'neutral'}
                      </span>
                      <span className="text-xs text-gray-500">•</span>
                      <span className="text-xs text-gray-400">{article.source}</span>
                      <span className="text-xs text-gray-500">•</span>
                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock size={12} />
                        {formatTime(article.published_at)}
                      </span>
                    </div>
                    
                    <h3 className="text-lg font-medium mb-2 group-hover:text-blue-400 transition-colors">
                      {article.headline}
                    </h3>
                    
                    {article.summary && (
                      <p className="text-sm text-gray-400 line-clamp-2">
                        {article.summary}
                      </p>
                    )}
                  </div>
                  
                  <a
                    href={article.url || `https://www.google.com/search?q=${encodeURIComponent(article.headline)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 bg-[#21262d] rounded-lg hover:bg-[#30363d] transition-colors opacity-0 group-hover:opacity-100"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <ExternalLink size={16} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
