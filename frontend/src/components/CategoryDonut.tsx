import { Cell, Pie, PieChart } from 'recharts'
import { OTHER_COLOR, seriesColor } from '../lib/chartColors'

export interface DonutSlice {
  key: string
  name: string
  value: number // 표시용 숫자 (백엔드 계산 결과 그대로)
  percentage: number // 백엔드가 계산한 비중
  rank: number // 0부터; MAX_SLICES 이상은 '그 외'
  isOther?: boolean
}

interface Props {
  slices: DonutSlice[]
  activeKey: string | null
  onActiveChange: (key: string | null) => void
  emptyLabel: string
  size?: number
}

/** 참고 앱 스타일의 도넛. 가운데에는 활성(호버) 조각, 없으면 1위 조각의 이름과 비중을 보여 준다.
 *  조각 사이 2px 간격, 색은 순위별 고정 슬롯. 범례 역할은 아래 목록이 한다. */
export function CategoryDonut({ slices, activeKey, onActiveChange, emptyLabel, size = 260 }: Props) {
  const active = slices.find((s) => s.key === activeKey) ?? slices[0]
  const outer = size / 2 - 6
  const inner = outer * 0.62

  if (slices.length === 0) {
    return (
      <div className="flex items-center justify-center" style={{ width: size, height: size }}>
        <div
          className="flex items-center justify-center rounded-full border-[18px] border-gray-100 text-sm text-gray-400"
          style={{ width: outer * 2, height: outer * 2 }}
        >
          {emptyLabel}
        </div>
      </div>
    )
  }

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <PieChart width={size} height={size}>
        <Pie
          data={slices}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={inner}
          outerRadius={outer}
          startAngle={90}
          endAngle={-270}
          paddingAngle={slices.length > 1 ? 2 : 0}
          cornerRadius={3}
          stroke="none"
          isAnimationActive={false}
          onMouseEnter={(_, index) => onActiveChange(slices[index]?.key ?? null)}
          onMouseLeave={() => onActiveChange(null)}
        >
          {slices.map((s) => (
            <Cell
              key={s.key}
              fill={s.isOther ? OTHER_COLOR : seriesColor(s.rank)}
              fillOpacity={activeKey === null || activeKey === s.key ? 1 : 0.35}
              style={{ cursor: 'pointer', outline: 'none', transition: 'fill-opacity 120ms' }}
            />
          ))}
        </Pie>
      </PieChart>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="max-w-[60%] truncate text-sm font-medium text-gray-700">{active.name}</div>
        <div className="mt-0.5 text-2xl font-bold tabular-nums text-gray-900">{active.percentage}%</div>
      </div>
    </div>
  )
}
