interface Props {
  label: string
  value: string
  tone?: 'default' | 'positive' | 'negative'
  sub?: string
}

const toneClass: Record<NonNullable<Props['tone']>, string> = {
  default: 'text-gray-900',
  positive: 'text-emerald-600',
  negative: 'text-rose-600',
}

export function StatCard({ label, value, tone = 'default', sub }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="text-sm text-gray-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${toneClass[tone]}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-gray-400">{sub}</div>}
    </div>
  )
}
