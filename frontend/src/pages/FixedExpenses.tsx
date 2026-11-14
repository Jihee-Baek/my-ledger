import { Fragment, useState } from 'react'
import { endpoints } from '../api/endpoints'
import type { FixedExpenseCandidate, FixedExpenseRow, FixedExpenseStatus } from '../api/types'
import { CategoryBarList } from '../components/CategoryBarList'
import { MonthNav } from '../components/MonthNav'
import { StatCard } from '../components/StatCard'
import { errorDetail } from '../components/TransactionDetailModal'
import { useApiQuery } from '../hooks/useApiQuery'
import { formatAmount, toNumber } from '../lib/format'

const STATUS: Record<FixedExpenseStatus, { label: string; className: string }> = {
  paid: { label: '납부 완료', className: 'bg-emerald-50 text-emerald-700' },
  upcoming: { label: '예정', className: 'bg-gray-100 text-gray-600' },
  unconfirmed: { label: '미확인', className: 'bg-amber-50 text-amber-700' },
  missing: { label: '내역 없음', className: 'bg-rose-50 text-rose-600' },
}

const monthLabel = (ym: string) => `${Number(ym.slice(5, 7))}월`
const won = (v: string) => formatAmount(v).replace('원', '')

/**
 * 고정 지출: 등록된 항목별 최근 6개월 납부 현황을 한 표로. 합계·상태 판정은 전부 백엔드가 한다.
 */
export function FixedExpenses() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [form, setForm] = useState({ name: '', keyword: '', amount: '' })
  const [showForm, setShowForm] = useState(false)

  const data = useApiQuery(() => endpoints.fixedExpenseOverview(year, month), [year, month])
  const o = data.data

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    setError(null)
    try {
      await fn()
      data.reload()
    } catch (e) {
      setError(errorDetail(e))
    } finally {
      setBusy(false)
    }
  }

  const addCandidate = (c: FixedExpenseCandidate) =>
    run(() =>
      endpoints.createFixedExpense({
        name: c.name,
        keyword: c.keyword,
        card_id: c.card_id,
        amount: c.amount_filter,
        category_id: c.category_id,
      }),
    )

  const remove = (row: FixedExpenseRow) => run(() => endpoints.deleteFixedExpense(row.id))

  const addManual = () =>
    run(async () => {
      await endpoints.createFixedExpense({
        name: form.name.trim(),
        keyword: form.keyword.trim() || form.name.trim(),
        amount: form.amount ? Number(form.amount) : null,
      })
      setForm({ name: '', keyword: '', amount: '' })
      setShowForm(false)
    })

  // 표는 상위 카테고리별로 묶어 보여준다 (정렬은 백엔드가 그룹 > 결제일 순으로 해 둠)
  const groups: { group: string; rows: FixedExpenseRow[] }[] = []
  for (const row of o?.items ?? []) {
    const last = groups[groups.length - 1]
    if (last && last.group === row.category_group) last.rows.push(row)
    else groups.push({ group: row.category_group, rows: [row] })
  }
  const selectedKey = `${year}-${String(month).padStart(2, '0')}`

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">고정 지출</h1>
        <MonthNav
          year={year}
          month={month}
          onChange={(y, m) => {
            setYear(y)
            setMonth(m)
          }}
        />
      </div>

      {data.error && <div className="text-sm text-rose-600">데이터를 불러오지 못했습니다: {data.error}</div>}
      {error && <div className="text-sm text-rose-600">처리하지 못했습니다: {error}</div>}

      {o && (
        <>
          <div className="grid items-start gap-4 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <StatCard
                label="월 고정 지출"
                value={formatAmount(o.expected_monthly_total)}
                sub={`${o.item_count}개 항목 · 항목별 최근 납부액 합계`}
              />
              <StatCard
                label={`${month}월 납부 완료`}
                value={formatAmount(o.selected_paid_total)}
                tone="positive"
                sub={`${o.paid_count} / ${o.item_count}개`}
              />
              <StatCard
                label={`${month}월 남은 예정`}
                value={formatAmount(o.selected_remaining_total)}
                sub={`${o.item_count - o.paid_count}개 · 최근 납부액 기준`}
              />
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h2 className="mb-3 text-sm font-semibold text-gray-700">분류별 비중</h2>
              <CategoryBarList
                items={o.group_totals.map((g) => ({ category: g.group, amount: g.amount, percentage: g.percentage }))}
                emptyMessage="등록된 고정 지출이 없습니다."
              />
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
            <table className="w-full min-w-[860px] text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-gray-500">
                <tr>
                  <th className="px-4 py-2 text-left">항목</th>
                  <th className="px-3 py-2 text-left">결제일</th>
                  {o.months.map((m) => (
                    <th key={m} className={`px-3 py-2 text-right ${m === selectedKey ? 'text-gray-900' : ''}`}>
                      {monthLabel(m)}
                    </th>
                  ))}
                  <th className="px-3 py-2 text-left">{month}월 상태</th>
                  <th className="px-2 py-2" />
                </tr>
              </thead>
              <tbody>
                {groups.map(({ group, rows }) => (
                  <Fragment key={group}>
                    <tr className="bg-gray-50/60">
                      <td colSpan={o.months.length + 4} className="px-4 py-1.5 text-xs font-semibold text-gray-500">
                        {group}
                      </td>
                    </tr>
                    {rows.map((r) => (
                      <tr key={r.id} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="px-4 py-2">
                          <div className="font-medium text-gray-800">{r.name}</div>
                          <div className="text-xs text-gray-400">
                            {[r.card_label, r.category].filter(Boolean).join(' · ') || '-'}
                            {r.memo && ` · ${r.memo}`}
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-gray-600">{r.pay_day ? `매월 ${r.pay_day}일` : '-'}</td>
                        {r.monthly.map((m) => (
                          <td
                            key={m.month}
                            className={`whitespace-nowrap px-3 py-2 text-right tabular-nums ${
                              m.month === selectedKey ? 'bg-gray-50 font-medium text-gray-900' : 'text-gray-600'
                            }`}
                            title={m.count > 1 ? `${m.count}건 합계` : undefined}
                          >
                            {toNumber(m.amount) ? won(m.amount) : <span className="text-gray-300">—</span>}
                          </td>
                        ))}
                        <td className="whitespace-nowrap px-3 py-2">
                          <span className={`rounded px-1.5 py-0.5 text-xs ${STATUS[r.status].className}`}>
                            {STATUS[r.status].label}
                            {r.status === 'upcoming' && r.pay_day ? ` · ${r.pay_day}일` : ''}
                          </span>
                        </td>
                        <td className="px-2 py-2 text-right">
                          <button
                            disabled={busy}
                            onClick={() => remove(r)}
                            className="rounded px-1.5 text-gray-300 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-40"
                            aria-label={`${r.name} 삭제`}
                            title="고정 지출에서 빼기 (거래내역은 그대로)"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </Fragment>
                ))}
                {o.items.length === 0 && (
                  <tr>
                    <td colSpan={o.months.length + 4} className="px-4 py-8 text-center text-gray-400">
                      등록된 고정 지출이 없습니다. 아래 추천 항목에서 추가해 보세요.
                    </td>
                  </tr>
                )}
              </tbody>
              {o.items.length > 0 && (
                <tfoot className="border-t border-gray-200 bg-gray-50 font-medium">
                  <tr>
                    <td className="px-4 py-2" colSpan={2}>
                      월 합계
                    </td>
                    {o.monthly_totals.map((m) => (
                      <td
                        key={m.month}
                        className={`whitespace-nowrap px-3 py-2 text-right tabular-nums ${m.month === selectedKey ? 'text-gray-900' : 'text-gray-600'}`}
                      >
                        {won(m.amount)}
                      </td>
                    ))}
                    <td colSpan={2} />
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
          <p className="-mt-2 text-xs text-gray-400">
            미확인은 결제일이 지났지만 아직 가져온 내역에 없는 항목입니다. 해당 은행·카드 내역을 가져오면 납부 완료로 바뀝니다.
          </p>

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-sm font-semibold text-gray-700">고정 지출로 보이는 항목</h2>
              <button
                onClick={() => setShowForm(!showForm)}
                className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-100"
              >
                {showForm ? '닫기' : '+ 직접 추가'}
              </button>
            </div>

            {showForm && (
              <div className="mb-4 flex flex-wrap items-center gap-2 rounded-md bg-gray-50 p-3 text-sm">
                <input
                  placeholder="이름 (예: 넷플릭스)"
                  className="rounded-md border border-gray-300 px-2 py-1"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
                <input
                  placeholder="가맹점 키워드 (비우면 이름)"
                  className="rounded-md border border-gray-300 px-2 py-1"
                  value={form.keyword}
                  onChange={(e) => setForm({ ...form, keyword: e.target.value })}
                />
                <input
                  type="number"
                  placeholder="금액 (같은 이름이 여러 건일 때만)"
                  className="w-56 rounded-md border border-gray-300 px-2 py-1"
                  value={form.amount}
                  onChange={(e) => setForm({ ...form, amount: e.target.value })}
                />
                <button
                  disabled={busy || !form.name.trim()}
                  onClick={addManual}
                  className="rounded-md bg-gray-900 px-3 py-1 text-white disabled:opacity-40"
                >
                  추가
                </button>
              </div>
            )}

            {o.candidates.length === 0 ? (
              <div className="py-4 text-center text-sm text-gray-400">추천할 항목이 없습니다.</div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {o.candidates.map((c) => (
                  <li key={`${c.keyword}-${c.card_id}-${c.amount_filter}`} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                    <div>
                      <span className="font-medium text-gray-800">{c.name}</span>
                      <span className="ml-2 text-xs text-gray-400">
                        {[c.card_label, c.category, `매월 ${c.pay_day}일쯤`, `최근 6개월 중 ${c.months_seen}개월`].filter(Boolean).join(' · ')}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="tabular-nums text-gray-600">{formatAmount(c.typical_amount)}</span>
                      <button
                        disabled={busy}
                        onClick={() => addCandidate(c)}
                        className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-100 disabled:opacity-40"
                      >
                        추가
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  )
}
