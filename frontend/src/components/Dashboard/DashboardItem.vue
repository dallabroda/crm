<template>
  <div class="h-full w-full">
    <div
      v-if="item.type == 'number_chart'"
      class="ct-metric flex h-full w-full overflow-hidden cursor-pointer"
    >
      <Tooltip :text="__(item.data.tooltip)">
        <NumberCard
          v-if="item.data"
          :key="index"
          class="h-full"
          v-bind="numberCardProps"
        />
      </Tooltip>
    </div>
    <div
      v-else-if="item.type == 'spacer'"
      class="rounded-4 bg-surface-base h-full overflow-hidden text-ink-gray-5 flex items-center justify-center"
      :class="editing ? 'border border-dashed border-outline-gray-2' : ''"
    >
      {{ editing ? __('Spacer') : '' }}
    </div>
    <ChartCard v-else-if="item.type == 'axis_chart'" class="h-full">
      <component
        :is="axisChart.component"
        v-if="item.data"
        v-bind="axisChart.props"
      >
        <template #empty>
          <ChartEmptyState
            :kind="axisChart.props.horizontal ? 'rows' : 'bars'"
          />
        </template>
      </component>
    </ChartCard>
    <ChartCard v-else-if="item.type == 'donut_chart'" class="ct-donut h-full">
      <DonutChart v-if="item.data" v-bind="donutChartProps">
        <template #empty>
          <ChartEmptyState kind="donut" />
        </template>
      </DonutChart>
    </ChartCard>
  </div>
</template>
<script setup lang="ts">
import { Tooltip } from 'frappe-ui'
import ChartEmptyState from '@/components/Dashboard/ChartEmptyState.vue'
import {
  AreaChart,
  BarChart,
  ChartCard,
  DonutChart,
  LineChart,
  NumberCard,
} from 'frappe-ui/charts'
import {
  type AxisChartConfig,
  type AxisChartKind,
  type DashboardChartConfig,
  type DonutChartConfig,
  type NumberChartConfig,
  getAxisChartKind,
  toAxisChartProps,
  toDonutChartProps,
  toNumberCardProps,
} from '@/utils/dashboardCharts'
import { computed, type Component } from 'vue'

const props = withDefaults(
  defineProps<{
    index: number
    item: { name?: string; type: string; data?: DashboardChartConfig | null }
    editing?: boolean
  }>(),
  { editing: false },
)

const axisChartComponents: Record<AxisChartKind, Component> = {
  line: LineChart,
  area: AreaChart,
  bar: BarChart,
}

const config = computed<DashboardChartConfig>(() => props.item.data || {})

// Figma "Legenda de gráfico": the CredTech blue scale (Azul 2, Azul 3,
// Azul 4, then the darker blue and gray). Read from the --ct-chart-* tokens
// as concrete colors, since echarts cannot resolve CSS variables. A chart
// whose config sets its own colors keeps them.
const CHART_TOKENS = [
  '--ct-chart-2',
  '--ct-chart-3',
  '--ct-chart-4',
  '--ct-chart-1',
  '--ct-chart-5',
]
const FALLBACK_PALETTE = ['#0088ff', '#66b8ff', '#b3dbff', '#0070e0', '#dcdde2']
function ctPalette() {
  const styles = getComputedStyle(document.documentElement)
  return CHART_TOKENS.map(
    (name, i) => styles.getPropertyValue(name).trim() || FALLBACK_PALETTE[i],
  )
}

const numberCardProps = computed(() =>
  toNumberCardProps(config.value as NumberChartConfig),
)
const donutChartProps = computed(() => {
  const donut = toDonutChartProps(config.value as DonutChartConfig)
  return {
    ...donut,
    palette: donut.palette?.length ? donut.palette : ctPalette(),
  }
})
// Figma draws every bar of a series in one blue: drop the server's
// per-bar coloring (`colorBy: 'data'`), which cycles through the palette.
function singleColorSeries(props: ReturnType<typeof toAxisChartProps>) {
  for (const style of Object.values(props.seriesConfig || {})) {
    if (style.echartOptions?.colorBy === 'data') {
      const rest = { ...style.echartOptions }
      delete rest.colorBy
      style.echartOptions = rest
    }
  }
  return props
}

const axisChart = computed(() => ({
  component:
    axisChartComponents[getAxisChartKind(config.value as AxisChartConfig)],
  props: {
    palette: ctPalette(),
    ...singleColorSeries(toAxisChartProps(config.value as AxisChartConfig)),
  },
}))
</script>

<style scoped>
/* Figma "Painel · Visão geral" donut cards: a 164px ring with the legend
   stacked on its right ("Gráfico e legenda") */
.ct-donut :deep([data-slot='chart-container']) {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-rows: auto minmax(0, 1fr);
  column-gap: 24px;
  row-gap: 6px;
}
.ct-donut :deep([data-slot='chart-header']) {
  grid-column: 1 / -1;
}
.ct-donut :deep([data-slot='chart-plot']) {
  grid-column: 1;
  align-self: center;
  height: 100%;
  max-height: 182px;
  padding-bottom: 0;
}
.ct-donut :deep([data-slot='chart-legend']) {
  grid-column: 2;
  grid-row: 2;
  align-self: center;
  flex-direction: column;
  flex-wrap: nowrap;
  align-items: flex-start;
  gap: 4px;
  padding-right: 8px;
}

/* Figma "Métrica": label on top, value (26/500) with the variation
   (12/600) beside it */
/* (the Tooltip around the card renames its data-slot to "trigger") */
.ct-metric > :deep(div) {
  border-radius: var(--ct-radius-lg);
  border-color: var(--ct-border);
  padding: 12px 16px;
}
.ct-metric > :deep(div > .flex-col) {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  column-gap: 8px;
  row-gap: 4px;
}
.ct-metric > :deep(div > .flex-col > :first-child) {
  grid-column: 1 / -1;
}
.ct-metric :deep(.text-3xl-semibold) {
  font-size: 26px;
  line-height: 32px;
  font-weight: 500;
}
.ct-metric :deep(.text-3xl-semibold + .text-sm) {
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
}
.ct-metric :deep(.text-sm.text-ink-gray-5) {
  font-weight: 500;
}
</style>
