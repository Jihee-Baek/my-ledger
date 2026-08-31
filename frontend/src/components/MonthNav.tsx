interface Props {
  year: number
  month: number
  onChange: (year: number, month: number) => void
}

export function MonthNav({ year, month, onChange }: Props) {
  const go = (delta: number) => {
    let y = year
    let m = month + delta
    if (m === 0) {
      m = 12
      y -= 1
    } else if (m === 13) {
      m = 1
      y += 1
    }
    onChange(y, m)
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={() => go(-1)}
        className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
        aria-label="이전 달"
      >
        ‹
      </button>
      <div className="w-28 text-center text-lg font-semibold">
        {year}년 {month}월
      </div>
      <button
        onClick={() => go(1)}
        className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
        aria-label="다음 달"
      >
        ›
      </button>
    </div>
  )
}
