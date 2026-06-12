export type FilterOp = 'eq' | 'neq' | 'gte' | 'lte' | 'gt' | 'lt' | 'contains' | 'between'

export interface ScreenerFilter {
  field: string
  op: FilterOp
  value: number | string | [number, number]
}

export interface ScreenerConfig {
  id?: number
  title: string
  filters: ScreenerFilter[]
  logic: 'AND' | 'OR'
  columns: string[]
  sort: { field: string; direction: 'asc' | 'desc' } | null
  limit: number
}

export type BuilderType = 'screener'

export interface BuilderState {
  type: BuilderType
  config: ScreenerConfig
  isDirty: boolean
  savedId: number | null
}
