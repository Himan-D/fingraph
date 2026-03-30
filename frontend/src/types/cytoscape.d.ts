declare module 'react-cytoscapejs' {
  import * as React from 'react'
  import cytoscape, { Core, ElementDefinition } from 'cytoscape'

  interface CytoscapeComponentProps {
    elements: ElementDefinition[]
    stylesheet?: any[]
    style?: React.CSSProperties
    cy?: (cy: Core) => void
    layout?: any
    wheelSensitivity?: number
    minZoom?: number
    maxZoom?: number
  }

  const CytoscapeComponent: React.FC<CytoscapeComponentProps>
  export default CytoscapeComponent
}
