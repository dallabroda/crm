// Chart resolvers (CRM's and contributed apps') return the experimental config shape; these map it to frappe-ui/charts props.
import type {
  BarChartProps,
  ChartValueAxisOptions,
  DonutChartProps,
  NumberCardProps,
  SeriesStyle,
  TimeGrain,
} from 'frappe-ui/charts'

type Row = Record<string, unknown>

interface ValueAxisConfig {
  title?: string
  yMin?: number
  yMax?: number
  echartOptions?: Row
}

interface SeriesConfig {
  name: string
  // Display name, already translated by the server; `name` stays the data key
  label?: string
  type: 'bar' | 'line' | 'area'
  color?: string
  axis?: 'y' | 'y2'
  showDataLabels?: boolean
  showDataPoints?: boolean
  lineType?: 'solid' | 'dashed' | 'dotted'
  stackName?: string
  echartOptions?: Row
}

export interface AxisChartConfig {
  data?: Row[]
  title?: string
  subtitle?: string
  colors?: string[]
  xAxis?: {
    key: string
    type?: 'category' | 'time' | 'value'
    timeGrain?: TimeGrain
    title?: string
    echartOptions?: Row
  }
  yAxis?: ValueAxisConfig
  y2Axis?: ValueAxisConfig
  swapXY?: boolean
  stacked?: boolean
  series?: SeriesConfig[]
  echartOptions?: Row
}

export interface DonutChartConfig {
  data?: Row[]
  title?: string
  subtitle?: string
  colors?: string[]
  categoryColumn: string
  valueColumn: string
  maxSliceCount?: number
  showInlineLabels?: boolean
  centerLabel?: string
  echartOptions?: Row
}

export type NumberChartConfig = NumberCardProps & { tooltip?: string }

export type DashboardChartConfig = Partial<
  NumberChartConfig & AxisChartConfig & DonutChartConfig
>

export type AxisChartKind = 'line' | 'area' | 'bar'

export function toNumberCardProps(config: NumberChartConfig): NumberCardProps {
  const props = { ...config }
  delete props.tooltip
  return props
}

// Same as frappe-ui's default; the chart's own "Others" slice is not translatable, so the tail
// is grouped here first, under a translated name, and the chart never needs to group it again.
const DONUT_MAX_SLICES = 9

function groupDonutTail(config: DonutChartConfig): Row[] {
  const { categoryColumn: category, valueColumn: value } = config
  const max = Math.max(2, config.maxSliceCount ?? DONUT_MAX_SLICES)
  const rows = (config.data || [])
    .filter((row) => Number(row[value]) >= 0)
    .sort((a, b) => Number(b[value]) - Number(a[value]))
  if (rows.length <= max) return rows
  const others = rows
    .slice(max - 1)
    .reduce((sum, row) => sum + Number(row[value]), 0)
  return [
    ...rows.slice(0, max - 1),
    { [category]: __('Others'), [value]: others },
  ]
}

export function toDonutChartProps(config: DonutChartConfig): DonutChartProps {
  return {
    title: config.title,
    subtitle: config.subtitle,
    data: groupDonutTail(config),
    category: config.categoryColumn,
    value: config.valueColumn,
    maxSlices: config.maxSliceCount,
    // Without it the ring's middle reads the value column's key ("Count")
    centerLabel: config.centerLabel ?? __('Total'),
    showDataLabels: config.showInlineLabels,
    palette: config.colors,
    echartOptions: config.echartOptions,
  }
}

export function getAxisChartKind(config: AxisChartConfig): AxisChartKind {
  const types = new Set((config.series || []).map((s) => s.type))
  if (types.size === 1 && types.has('line')) return 'line'
  if (types.size === 1 && types.has('area')) return 'area'
  return 'bar'
}

function toValueAxis(
  axis?: ValueAxisConfig,
): ChartValueAxisOptions | undefined {
  return (
    axis && {
      title: axis.title,
      min: axis.yMin,
      max: axis.yMax,
      echartOptions: axis.echartOptions,
    }
  )
}

export function toAxisChartProps(config: AxisChartConfig): BarChartProps {
  const series = config.series || []
  const seriesConfig: Record<string, SeriesStyle> = {}
  series.forEach((s, i) => {
    seriesConfig[s.name] = {
      label: s.label,
      type: s.type,
      color: s.color || config.colors?.[i],
      showDataLabels: s.showDataLabels,
      showDataPoints: s.showDataPoints,
      dashed: s.lineType === 'dashed' || s.lineType === 'dotted' || undefined,
      stackName: s.stackName,
      echartOptions: s.echartOptions,
    }
  })

  const y2 = series.filter((s) => s.axis === 'y2').map((s) => s.name)

  return {
    title: config.title,
    subtitle: config.subtitle,
    data: config.data || [],
    x: config.xAxis?.key as string,
    y: series.filter((s) => s.axis !== 'y2').map((s) => s.name),
    y2: y2.length ? y2 : undefined,
    seriesConfig,
    stacked: config.stacked,
    xAxis: {
      title: config.xAxis?.title,
      type: config.xAxis?.type,
      timeGrain: config.xAxis?.timeGrain,
      echartOptions: config.xAxis?.echartOptions,
    },
    yAxis: toValueAxis(config.yAxis),
    y2Axis: toValueAxis(config.y2Axis),
    echartOptions: config.echartOptions,
    ...(getAxisChartKind(config) === 'bar' && { horizontal: config.swapXY }),
  }
}
