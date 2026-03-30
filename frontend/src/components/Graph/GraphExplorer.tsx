import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'
import { Search, RefreshCw, ZoomIn, ZoomOut, Maximize2, Layout, Database, X } from 'lucide-react'

interface GraphNode {
  id: string
  label: string
  data: Record<string, unknown>
}

interface GraphEdge {
  from: string
  to: string
  type: string
  label: string
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

const GRAPH_STYLESHEET = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'font-size': '10px',
      'color': '#ffffff',
      'text-outline-width': 1,
      'text-outline-color': '#000000',
      'background-color': '#58a6ff',
      'width': 30,
      'height': 30,
      'border-width': 2,
      'border-color': '#1f6feb',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#58a6ff',
      'background-color': '#79c0ff',
    },
  },
  {
    selector: 'node.sector',
    style: {
      'background-color': '#238636',
      'border-color': '#2ea043',
      'width': 50,
      'height': 50,
      'font-size': '12px',
      'font-weight': 'bold',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 1,
      'line-color': '#30363d',
      'target-arrow-color': '#30363d',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
    },
  },
  {
    selector: 'edge.supplier',
    style: { 'line-color': '#3fb950' },
  },
  {
    selector: 'edge.customer',
    style: { 'line-color': '#58a6ff' },
  },
  {
    selector: 'edge.competitor',
    style: { 'line-color': '#f85149' },
  },
  {
    selector: 'edge.sector',
    style: { 'line-color': '#a371f7', 'line-style': 'dashed' },
  },
]

export default function GraphExplorer() {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'full' | 'company' | 'sector'>('full')
  const [stats, setStats] = useState({ nodes: 0, edges: 0, companies: 0, sectors: 0 })
  const [showSidebar] = useState(true)

  const fetchGraph = async (type: string, query?: string) => {
    setLoading(true)
    try {
      let url = `/api/v1/graph/${type}`
      if (query) url += `/${query}`
      
      const response = await axios.get(url)
      if (response.data.success) {
        setGraphData(response.data.data)
        
        const nodes = response.data.data.nodes || []
        const edges = response.data.data.edges || []
        const companies = nodes.filter((n: GraphNode) => n.label === 'Company').length
        const sectors = nodes.filter((n: GraphNode) => n.label === 'Sector').length
        setStats({ nodes: nodes.length, edges: edges.length, companies, sectors })
      }
    } catch (error) {
      console.error('Error fetching graph:', error)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchGraph('full')
  }, [])

  useEffect(() => {
    if (!containerRef.current || graphData.nodes.length === 0) return

    if (cyRef.current) {
      cyRef.current.destroy()
    }

    const elements: ElementDefinition[] = []
    
    graphData.nodes.forEach(node => {
      const isSector = node.label === 'Sector'
      elements.push({
        data: {
          id: node.id,
          label: node.id,
          nodeType: node.label,
        },
        classes: isSector ? 'sector' : 'company',
      })
    })
    
    graphData.edges.forEach(edge => {
      elements.push({
        data: {
          id: `${edge.from}-${edge.to}`,
          source: edge.from,
          target: edge.to,
          label: edge.type,
        },
        classes: edge.type.toLowerCase(),
      })
    })

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: GRAPH_STYLESHEET as any,
      layout: { name: 'cose', animate: false },
      minZoom: 0.1,
      maxZoom: 3,
    })

    cyRef.current.on('tap', 'node', (evt) => {
      setSelectedNode(evt.target.data())
    })

    cyRef.current.on('tap', 'edge', (evt) => {
      setSelectedNode({
        id: evt.target.id(),
        source: evt.target.data('source'),
        target: evt.target.data('target'),
        type: evt.target.data('label'),
      })
    })

    cyRef.current.on('tap', (evt) => {
      if (evt.target === cyRef.current) {
        setSelectedNode(null)
      }
    })

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
        cyRef.current = null
      }
    }
  }, [graphData])

  const handleSearch = (e?: React.FormEvent) => {
    e?.preventDefault()
    if (searchQuery) {
      setViewMode('company')
      fetchGraph('company', searchQuery.toUpperCase())
    }
  }

  const handleZoomIn = () => cyRef.current?.zoom((cyRef.current.zoom() || 1) * 1.3)
  const handleZoomOut = () => cyRef.current?.zoom((cyRef.current.zoom() || 1) * 0.7)
  const handleFit = () => cyRef.current?.fit(undefined, 50)
  
  const handleLayout = (layoutName: string = 'cose') => {
    cyRef.current?.layout({
      name: layoutName,
      animate: false,
      padding: 50,
    } as any).run()
  }

  const viewCompanyGraph = (symbol: string) => {
    setSearchQuery(symbol)
    fetchGraph('company', symbol)
    setViewMode('company')
  }

  return (
    <div className="flex flex-col h-full bg-terminal-bg">
      <div className="flex items-center gap-4 p-3 border-b border-terminal-border bg-terminal-card">
        <div className="flex items-center gap-2">
          <Database size={20} className="text-terminal-accent" />
          <h2 className="font-semibold">Knowledge Graph</h2>
        </div>
        
        <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2 max-w-md">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" size={16} />
            <input
              type="text"
              placeholder="Search company or sector..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 bg-terminal-bg border border-terminal-border rounded-lg text-sm"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/80"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-1 bg-terminal-bg rounded-lg p-1">
          <button
            onClick={() => { setViewMode('full'); fetchGraph('full'); setSearchQuery(''); }}
            className={`px-3 py-1 rounded text-xs font-medium ${viewMode === 'full' ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
          >
            Full Graph
          </button>
          <button
            onClick={() => { setViewMode('company'); fetchGraph('company', 'RELIANCE'); setSearchQuery('RELIANCE'); }}
            className={`px-3 py-1 rounded text-xs font-medium ${viewMode === 'company' ? 'bg-terminal-accent text-white' : 'text-terminal-muted hover:text-terminal-text'}`}
          >
            Company
          </button>
        </div>

        <div className="flex items-center gap-1">
          <button onClick={handleZoomIn} className="p-1.5 hover:bg-terminal-border rounded" title="Zoom In">
            <ZoomIn size={16} />
          </button>
          <button onClick={handleZoomOut} className="p-1.5 hover:bg-terminal-border rounded" title="Zoom Out">
            <ZoomOut size={16} />
          </button>
          <button onClick={handleFit} className="p-1.5 hover:bg-terminal-border rounded" title="Fit to View">
            <Maximize2 size={16} />
          </button>
          <div className="w-px h-4 bg-terminal-border mx-1" />
          <button onClick={() => handleLayout('cose')} className="p-1.5 hover:bg-terminal-border rounded" title="Spring Layout">
            <Layout size={16} />
          </button>
          <button onClick={() => handleLayout('circle')} className="p-1.5 hover:bg-terminal-border rounded" title="Circle Layout">
            <Layout size={16} />
          </button>
          <div className="w-px h-4 bg-terminal-border mx-1" />
          <button onClick={() => fetchGraph(viewMode, searchQuery || undefined)} className="p-1.5 hover:bg-terminal-border rounded" title="Refresh">
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 relative">
          {loading ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-terminal-bg/80 z-10">
              <div className="animate-spin rounded-full h-10 w-10 border-2 border-terminal-accent border-t-transparent mb-3"></div>
              <div className="text-terminal-muted">Loading Knowledge Graph...</div>
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-terminal-muted">
              <Database size={48} className="mb-4 opacity-50" />
              <p>No graph data available</p>
              <button 
                onClick={() => fetchGraph('full')}
                className="mt-4 px-4 py-2 bg-terminal-accent text-white rounded-lg"
              >
                Load Graph
              </button>
            </div>
          ) : (
            <div ref={containerRef} className="w-full h-full" />
          )}
          
          <div className="absolute top-3 left-3 bg-terminal-card/90 backdrop-blur border border-terminal-border rounded-lg p-2 text-xs">
            <div className="flex gap-3">
              <div><span className="text-terminal-muted">Nodes:</span> <span className="font-semibold">{stats.nodes}</span></div>
              <div><span className="text-terminal-muted">Edges:</span> <span className="font-semibold">{stats.edges}</span></div>
              <div><span className="text-terminal-muted">Companies:</span> <span className="font-semibold text-[#58a6ff]">{stats.companies}</span></div>
              <div><span className="text-terminal-muted">Sectors:</span> <span className="font-semibold text-[#3fb950]">{stats.sectors}</span></div>
            </div>
          </div>
        </div>
        
        {showSidebar && selectedNode && (
          <div className="w-80 bg-terminal-card border-l border-terminal-border flex flex-col">
            <div className="p-4 border-b border-terminal-border">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-sm">Node Details</h3>
                <button onClick={() => setSelectedNode(null)} className="p-1 hover:bg-terminal-border rounded">
                  <X size={14} />
                </button>
              </div>
              
              <div className="space-y-3">
                <div>
                  <span className="text-xs text-terminal-muted">ID</span>
                  <div className="font-mono font-medium">{selectedNode.id || selectedNode.label}</div>
                </div>
                <div>
                  <span className="text-xs text-terminal-muted">Type</span>
                  <div className="font-medium">{selectedNode.nodeType || 'Edge'}</div>
                </div>
                {selectedNode.source && (
                  <div>
                    <span className="text-xs text-terminal-muted">Source</span>
                    <div className="font-mono">{selectedNode.source}</div>
                  </div>
                )}
                {selectedNode.target && (
                  <div>
                    <span className="text-xs text-terminal-muted">Target</span>
                    <div className="font-mono">{selectedNode.target}</div>
                  </div>
                )}
                {selectedNode.label && selectedNode.nodeType && (
                  <button
                    onClick={() => viewCompanyGraph(selectedNode.id)}
                    className="w-full mt-2 px-3 py-2 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/80"
                  >
                    View in Graph
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 p-4 overflow-auto">
              <h4 className="text-xs font-semibold text-terminal-muted mb-2">Legend</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-[#238636]"></div>
                  <span className="text-xs">Sector</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-[#58a6ff]"></div>
                  <span className="text-xs">Company</span>
                </div>
              </div>

              <h4 className="text-xs font-semibold text-terminal-muted mb-2 mt-4">Relationships</h4>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-[#3fb950]"></div>
                  <span className="text-xs">Supplier</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-[#58a6ff]"></div>
                  <span className="text-xs">Customer</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-[#f85149]"></div>
                  <span className="text-xs">Competitor</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-0.5 bg-[#a371f7] border-dashed border-t"></div>
                  <span className="text-xs">Sector</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
