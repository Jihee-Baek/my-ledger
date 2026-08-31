import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { toNumber } from '../lib/format'
import type { MonthlyTrendItem } from '../api/types'

export function TrendChart({ items }: { items: MonthlyTrendItem[] }) {
  const data = items.map((item) => ({
    label: `${item.month}월`,
    expense: toNumber(item.total_expense),
    income: toNumber(item.total_income),
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
        <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} stroke="#9ca3af" />
        <YAxis
          tickLine={false}
          axisLine={false}
          fontSize={12}
          stroke="#9ca3af"
          tickFormatter={(v: number) => (v >= 10000 ? `${Math.round(v / 10000)}만` : String(v))}
        />
        <Tooltip
          formatter={(value) => Number(Array.isArray(value) ? value[0] : value).toLocaleString('ko-KR') + '원'}
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
        />
        <Bar dataKey="expense" name="지출" fill="#111827" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
