import { useState } from 'react'
import { endpoints } from '../api/endpoints'
import { AiAnalysisPanel } from '../components/AiAnalysisPanel'
import { CategoryBarList } from '../components/CategoryBarList'
import { MonthNav } from '../components/MonthNav'
import { RecentTransactions } from '../components/RecentTransactions'
import { StatCard } from '../components/StatCard'
import { TrendChart } from '../components/TrendChart'
import { useApiQuery } from '../hooks/useApiQuery'
import { formatAmount, formatPercent, monthRange, toNumber } from '../lib/format'

function prevMonth(year: number, month: number): [number, number] {
  return month === 1 ? [year - 1, 12] : [year, month - 1]
}


export function Dashboard() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [prevYear, prevMonthNum] = prevMonth(year, month)
  const [start, end] = monthRange(year, month)

  const summary = useApiQuery(() => endpoints.monthlySummary(year, month), [year, month])
  const prevSummary = useApiQuery(() => endpoints.monthlySummary(prevYear, prevMonthNum), [prevYear, prevMonthNum])
  const trend = useApiQuery(() => endpoints.trend(6, year, month), [year, month])
  const recent = useApiQuery(
    () => endpoints.transactions({ start_date: start, end_date: end, limit: 6 }),
    [start, end],
  )
  const anomalies = useApiQuery(() => endpoints.anomalies(year, month), [year, month])

  const loading = summary.loading || !summary.data

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <MonthNav year={year} month={month} onChange={(y, m) => { setYear(y); setMonth(m) }} />
      </div>

      {summary.error && <div className="text-sm text-rose-600">데이터를 불러오지 못했습니다: {summary.error}</div>}

      {!loading && summary.data && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <StatCard label="총수입" value={formatAmount(summary.data.total_income)} />
            <StatCard label="총지출" value={formatAmount(summary.data.total_expense)} tone="negative" />
            <StatCard
              label="순수입"
              value={formatAmount(summary.data.net)}
              tone={toNumber(summary.data.net) >= 0 ? 'positive' : 'negative'}
            />
            <StatCard
              label="거래 건수"
              value={`${recent.data?.total ?? '-'}건`}
              sub={
                !prevSummary.loading && prevSummary.data
                  ? (() => {
                      const prevExpense = toNumber(prevSummary.data!.total_expense)
                      const curExpense = toNumber(summary.data!.total_expense)
                      const pct = prevExpense ? ((curExpense - prevExpense) / prevExpense) * 100 : null
                      return `전월 대비 지출 ${formatPercent(pct)}`
                    })()
                  : undefined
              }
            />
          </div>

          {summary.data.other_currencies.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
              해외 통화 지출 별도:{' '}
              {summary.data.other_currencies.map((c) => `${formatAmount(c.total_expense, c.currency)}`).join(', ')}
            </div>
          )}

          <AiAnalysisPanel year={year} month={month} anomalies={anomalies.data} loading={anomalies.loading} />

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-gray-700">최근 6개월 지출 추이</h2>
            {trend.data && <TrendChart items={trend.data} />}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold text-gray-700">카테고리별 지출</h2>
              <CategoryBarList items={summary.data.top_categories} />
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold text-gray-700">최근 거래</h2>
              {recent.data && <RecentTransactions items={recent.data.items} />}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
