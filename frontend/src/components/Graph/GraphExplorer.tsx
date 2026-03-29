import { useState, useEffect, useRef, useCallback } from 'react'
import axios from 'axios'
import CytoscapeComponent from 'react-cytoscapejs'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'
import { Search, RefreshCw, ZoomIn, ZoomOut, Focus, Share2, Layout } from 'lucide-react'

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

export default function GraphExplorer() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'full' | 'company' | 'sector'>('full')
  const [selectedNode, setSelectedNode] = useState<Record<string, unknown> | null>(null)
  const cyRef = useRef<Core | null>(null)

  const fetchGraph = async (type: string = 'full', param?: string) => {
    setLoading(true)
    try {
      let url = '/api/v1/graph/'
      if (type === 'full') url += 'full'
      else if (type === 'company' && param) url += `company/${param}`
      else if (type === 'sector' && param) url += `sector/${param}`
      else if (type === 'promoter' && param) url += `promoter/${param}`
      
      const response = await axios.get(url)
      if (response.data.success) {
        setGraphData(response.data.data)
      }
    } catch (error) {
      console.error('Error fetching graph:', error)
    }
    setLoading(false)
  }

  useEffect(() => {
    fetchGraph('full')
  }, [])

  const handleSearch = () => {
    if (searchQuery) {
      fetchGraph('company', searchQuery.toUpperCase())
    }
  }

  const transformToElements = useCallback((): ElementDefinition[] => {
    const elements: ElementDefinition[] = []
    
    graphData.nodes.forEach(node => {
      const isSector = node.label === 'Sector'
      const isCompany = node.label === 'Company'
      
      elements.push({
        data: {
          id: node.id,
          label: node.id,
          ...node.data,
          nodeType: node.label,
        },
        classes: isSector ? 'sector' : isCompany ? 'company' : 'other',
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
    
    return elements
  }, [graphData])

  const cyStylesheet: cytoscape.Stylesheet[] = [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'text-valign': 'bottom',
        'text-margin-y': 5,
        'font-size': '10px',
        'color': '#8b949e',
        'background-color': '#58a6ff',
        'width': 30,
        'height': 30,
      },
    },
    {
      selector: 'node.sector',
      style: {
        'background-color': '#3fb950',
        'width': 50,
        'height': 50,
        'font-size': '12px',
        'font-weight': 'bold',
      },
    },
    {
      selector: 'node.company',
      style: {
        'background-color': '#58a6ff',
        'width': 35,
        'height': 35,
      },
    },
    {
      selector: 'edge',
      style: {
        'width': 1,
        'line-color': '#30363d',
        'curve-style': 'bezier',
      },
    },
    {
      selector: 'edge.competitor',
      style: {
        'line-color': '#f85149',
        'target-arrow-color': '#f85149',
        'target-arrow-shape': 'triangle',
        'width': 2,
      },
    },
    {
      selector: 'edge.belongs_to_sector',
      style: {
        'line-color': '#3fb950',
        'target-arrow-color': '#3fb950',
        'target-arrow-shape': 'triangle',
        'width': 2,
      },
    },
    {
      selector: 'edge.same_group',
      style: {
        'line-color': '#d29922',
        'target-arrow-color': '#d29922',
        'target-arrow-shape': 'circle',
      },
    },
    {
      selector: ':selected',
      style: {
        'border-width': 3,
        'border-color': '#58a6ff',
      },
    },
  ]

  const handleCyReady = (cy: Core) => {
    cyRef.current = cy
    cy.on('tap', 'node', (evt) => {
      const node = evt.target
      setSelectedNode(node.data())
    })
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null)
      }
    })
  }

  const handleZoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2)
    }
  }

  const handleZoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 0.8)
    }
  }

  const handleFit = () => {
    if (cyRef.current) {
      cyRef.current.fit()
    }
  }

  const handleLayout = () => {
    if (cyRef.current) {
      cyRef.current.layout({
        name: 'cose',
        animate: true,
        nodeSpacing: 30,
      }).run()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-4 p-4 border-b border-terminal-border bg-terminal-card">
        <h2 className="text-lg font-semibold">Knowledge Graph</h2>
        
        {/* Search */}
        <div className="flex-1 flex items-center gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-terminal-muted" size={16} />
            <input
              type="text"
              placeholder="Search company, sector, promoter..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-9 pr-4 py-2 bg-terminal-bg border border-terminal-border rounded-lg text-sm"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-3 py-2 bg-terminal-accent text-white rounded-lg text-sm hover:bg-terminal-accent/80"
          >
            Search
          </button>
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setViewMode('full'); fetchGraph('full'); }}
            className={`px-3 py-1 rounded text-sm ${viewMode === 'full' ? 'bg-terminal-accent text-white' : 'bg-terminal-border'}`}
          >
            Full
          </button>
          <button
            onClick={() => { setViewMode('company'); fetchGraph('company', 'RELIANCE'); }}
            className={`px-3 py-1 rounded text-sm ${viewMode === 'company' ? 'bg-terminal-accent text-white' : 'bg-terminal-border'}`}
          >
            Company
          </button>
          <button
            onClick={() => { setViewMode('sector'); fetchGraph('sector', 'Technology'); }}
            className={`px-3 py-1 rounded text-sm ${viewMode === 'sector' ? 'bg-terminal-accent text-white' : 'bg-terminal-border'}`}
          >
            Sector
          </button>
        </div>

        {/* Graph Controls */}
        <div className="flex items-center gap-1">
          <button onClick={handleZoomIn} className="p-2 hover:bg-terminal-border rounded" title="Zoom In">
            <ZoomIn size={18} />
          </button>
          <button onClick={handleZoomOut} className="p-2 hover:bg-terminal-border rounded" title="Zoom Out">
            <ZoomOut size={18} />
          </button>
          <button onClick={handleFit} className="p-2 hover:bg-terminal-border rounded" title="Fit">
            <Focus size={18} />
          </button>
          <button onClick={handleLayout} className="p-2 hover:bg-terminal-border rounded" title="Auto Layout">
            <Layout size={18} />
          </button>
          <button onClick={() => fetchGraph(viewMode)} className="p-2 hover:bg-terminal-border rounded" title="Refresh">
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 flex">
        {/* Graph */}
        <div className="flex-1 bg-terminal-bg">
          {loading ? (
            <div className="flex items-center justify-center h-full text-terminal-muted">
              Loading graph...
            </div>
          ) : graphData.nodes.length === 0 ? (
            <div className="flex items-center justify-center h-full text-terminal-muted">
              No graph data available
            </div>
          ) : (
            <CytoscapeComponent
              elements={transformToElements()}
              stylesheet={cyStylesheet}
              style={{ width: '100%', height: '100%' }}
              cy={handleCyReady}
              layout={{ name: 'cose', nodeSpacing: 30, animate: true }}
            />
          )}
        </div>
        
        {/* Sidebar */}
        <div className="w-80 bg-terminal-card border-l border-terminal-border p-4 overflow-auto">
          <h3 className="font-semibold mb-4">Legend</h3>
          
          <div className="space-y-3 mb-6">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#3fb950]"></div>
              <span className="text-sm">Sector</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#58a6ff]"></div>
              <span className="text-sm">Company</span>
            </div>
          </div>

          <h3 className="font-semibold mb-4">Relationship Types</h3>
          
          <div className="space-y-3 mb-6">
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-[#f85149]"></div>
              <span className="text-sm">Competitor</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-[#3fb950]"></div>
              <span className="text-sm">Belongs to Sector</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-[#d29922]"></div>
              <span className="text-sm">Same Group</span>
            </div>
          </div>

          {selectedNode && (
            <div className="border-t border-terminal-border pt-4">
              <h4 className="font-semibold mb-3">{selectedNode.label || selectedNode.id}</h4>
              <div className="space-y-2 text-sm">
                {Object.entries(selectedNode)
                  .filter(([key]) => !['id', 'label', 'nodeType'].includes(key))
                  .slice(0, 8)
                  .map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-terminal-muted capitalize">{key.replace(/_/g, ' ')}:</span>
                      <span className="text-right max-w-[150px] truncate">
                        {typeof value === 'number' ? value.toLocaleString() : String(value)}
                      </span>
                    </div>
                  ))}
                <button
                  onClick={() => window.location.href = `/quotes?symbol=${selectedNode.id}`}
                  className="w-full mt-3 py-2 bg-terminal-accent text-white rounded text-sm hover:opacity-90"
                >
                  View Stock
                </button>
                <button
                  onClick={() => window.location.href = `/ai?symbol=${selectedNode.id}`}
                  className="w-full mt-2 py-2 bg-terminal-bg border border-terminal-border rounded text-sm hover:bg-terminal-border"
                >
                  Ask AI About This
                </button>
              </div>
            </div>
          )}

          <div className="border-t border-terminal-border pt-4 mt-4">
            <h4 className="font-semibold mb-2">Statistics</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="bg-terminal-bg p-2 rounded">
                <div className="text-terminal-muted text-xs">Nodes</div>
                <div className="font-semibold">{graphData.nodes.length}</div>
              </div>
              <div className="bg-terminal-bg p-2 rounded">
                <div className="text-terminal-muted text-xs">Edges</div>
                <div className="font-semibold">{graphData.edges.length}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
