import { formatAmount } from '../lib/format'
import type { CategoryAmount } from '../api/types'

export function CategoryBarList({ items }: { items: CategoryAmount[] }) {
  if (items.length === 0) {
    return <div className="py-6 text-center text-sm text-gray-400">이번 달 지출 내역이 없습니다.</div>
  }

  return (
    <div className="flex flex-col gap-3">
      {items.map((item) => (
        <div key={item.category}>
          <div className="mb-1 flex items-baseline justify-between text-sm">
            <span className="font-medium text-gray-700">{item.category}</span>
            <span className="tabular-nums text-gray-500">
              {formatAmount(item.amount)} · {item.percentage}%
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-gray-100">
            <div
              className="h-1.5 rounded-full bg-gray-900"
              style={{ width: `${Math.min(item.percentage, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
