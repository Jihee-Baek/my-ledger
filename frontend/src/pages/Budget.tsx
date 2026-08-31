import { useMemo, useState } from 'react'
import { endpoints } from '../api/endpoints'
import { MonthNav } from '../components/MonthNav'
import { useApiQuery } from '../hooks/useApiQuery'
import { flattenCategories } from '../lib/categoryTree'
import { formatAmount, toNumber } from '../lib/format'

export function Budget() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)

  const categories = useApiQuery(() => endpoints.categories(), [])
  const flatCategories = useMemo(() => (categories.data ? flattenCategories(categories.data) : []), [categories.data])
  const budgets = useApiQuery(() => endpoints.budgetStatus(year, month), [year, month])

  const [formCategoryId, setFormCategoryId] = useState('')
  const [formAmount, setFormAmount] = useState('')
  const [saving, setSaving] = useState(false)

  const save = async () => {
    if (!formAmount) return
    setSaving(true)
    try {
      await endpoints.setBudget(year, month, Number(formAmount), formCategoryId ? Number(formCategoryId) : null)
      setFormAmount('')
      setFormCategoryId('')
      budgets.reload()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">예산</h1>
        <MonthNav year={year} month={month} onChange={(y, m) => { setYear(y); setMonth(m) }} />
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-700">예산 설정</h2>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select
            className="rounded-md border border-gray-300 px-3 py-1.5"
            value={formCategoryId}
            onChange={(e) => setFormCategoryId(e.target.value)}
          >
            <option value="">전체 예산</option>
            {flatCategories.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
          <input
            type="number"
            placeholder="금액"
            className="w-32 rounded-md border border-gray-300 px-3 py-1.5"
            value={formAmount}
            onChange={(e) => setFormAmount(e.target.value)}
          />
          <button
            onClick={save}
            disabled={saving || !formAmount}
            className="rounded-md bg-gray-900 px-4 py-1.5 text-white disabled:opacity-40"
          >
            저장
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-700">{year}년 {month}월 예산 현황</h2>
        {budgets.data && budgets.data.length === 0 && (
          <div className="py-6 text-center text-sm text-gray-400">설정된 예산이 없습니다. 위에서 예산을 추가해보세요.</div>
        )}
        <div className="flex flex-col divide-y divide-gray-100">
          {budgets.data?.map((b) => {
            const remaining = toNumber(b.remaining)
            const over = remaining < 0
            return (
              <div key={`${b.category_id ?? 'total'}`} className="grid grid-cols-4 items-center gap-4 py-3 text-sm">
                <div className="font-medium text-gray-800">{b.category}</div>
                <div className="text-gray-500">예산 {formatAmount(b.budgeted)}</div>
                <div className="text-gray-500">지출 {formatAmount(b.actual)}</div>
                <div className={over ? 'text-right font-medium text-rose-600' : 'text-right font-medium text-emerald-600'}>
                  {over ? `초과 ${formatAmount(Math.abs(remaining))}` : `잔여 ${formatAmount(remaining)}`}
                  {b.percentage_used !== null && (
                    <span className="ml-2 text-xs font-normal text-gray-400">{b.percentage_used}%</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
