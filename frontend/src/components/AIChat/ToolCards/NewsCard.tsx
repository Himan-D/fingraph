import { Newspaper, ExternalLink, Clock } from 'lucide-react'

interface NewsItem {
  headline: string
  source?: string
  time?: string
  url?: string
  sentiment?: string
}

interface NewsCardProps {
  articles: NewsItem[]
}

export default function NewsCard({ articles }: NewsCardProps) {
  if (!articles.length) return null

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 p-3 border-b border-terminal-border bg-gradient-to-r from-orange-500/10 to-amber-500/10">
        <Newspaper size={16} className="text-orange-400" />
        <h3 className="font-semibold text-sm">News ({articles.length})</h3>
      </div>
      <div className="divide-y divide-terminal-border/50">
        {articles.slice(0, 8).map((article, i) => (
          <div key={i} className="p-3 hover:bg-terminal-bg/50 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium leading-snug line-clamp-2">{article.headline}</p>
                <div className="flex items-center gap-3 mt-1.5">
                  {article.source && (
                    <span className="text-[10px] uppercase text-terminal-muted tracking-wider">{article.source}</span>
                  )}
                  {article.time && (
                    <span className="flex items-center gap-1 text-[10px] text-terminal-muted">
                      <Clock size={10} />
                      {article.time}
                    </span>
                  )}
                  {article.sentiment && (
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      article.sentiment === 'positive' ? 'bg-green-500/20 text-green-400' :
                      article.sentiment === 'negative' ? 'bg-red-500/20 text-red-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {article.sentiment}
                    </span>
                  )}
                </div>
              </div>
              {article.url && (
                <a href={article.url} target="_blank" rel="noopener noreferrer"
                  className="p-1.5 hover:bg-terminal-border rounded-lg transition-colors flex-shrink-0">
                  <ExternalLink size={12} className="text-terminal-muted" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
