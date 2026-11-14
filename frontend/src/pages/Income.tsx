import { useMemo, useState } from 'react'
import { endpoints } from '../api/endpoints'
import type { TransactionOut } from '../api/types'
import { CategoryBarList } from '../components/CategoryBarList'
import { MonthNav } from '../components/MonthNav'
import { StatCard } from '../components/StatCard'
import { TransactionDetailModal, errorDetail } from '../components/TransactionDetailModal'
import { useApiQuery } from '../hooks/useApiQuery'
import { categoryNameMap, flattenCategories } from '../lib/categoryTree'
import { formatAmount, formatDate, isTransfer, monthRange } from '../lib/format'

const PAGE_SIZE = 50

type TypeFilter = '' | 'INCOME' | 'TRANSFER'

/**
 * 들어온 돈(direction=IN) 전체. 수입으로 잡힌 것과 이체로 빠진 것을 한 화면에서 보고,
 * 행마다 수입 <-> 이체를 바로 바꿀 수 있다. 합계·비중은 전부 백엔드가 계산한다.
 */
export function Income() {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth() + 1)
  const [allTime, setAllTime] = useState(false)
  const [typeFilter, setTypeFilter] = useState<TypeFilter>('')
  const [page, setPage] = useState(0)
  const [selected, setSelected] = useState<TransactionOut | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [monthStart, monthEnd] = monthRange(year, month)
  const startDate = allTime ? undefined : monthStart
  const endDate = allTime ? undefined : monthEnd

  const goMonth = (y: number, m: number) => {
    setYear(y)
    setMonth(m)
    setAllTime(false)
    setPage(0)
  }

  const categories = useApiQuery(() => endpoints.categories(), [])
  const cards = useApiQuery(() => endpoints.cards(), [])
  const flatCategories = useMemo(() => (categories.data ? flattenCategories(categories.data) : []), [categories.data])
  const catNameById = useMemo(() => (categories.data ? categoryNameMap(categories.data) : new Map<number, string>()), [categories.data])
  const cardLabelById = useMemo(() => {
    const map = new Map<number, string>()
    for (const c of cards.data ?? []) map.set(c.id, `${c.institution} ${c.card_number_masked ?? ''}`.trim())
    return map
  }, [cards.data])

  const list = useApiQuery(
    () =>
      endpoints.transactions({
        start_date: startDate,
        end_date: endDate,
        direction: 'IN',
        transaction_type: typeFilter || undefined,
        sort_by: 'date',
        sort_dir: 'desc',
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    [startDate, endDate, typeFilter, page],
  )

  const summary = useApiQuery(
    () => endpoints.transactionSummary({ start_date: startDate, end_date: endDate, direction: 'IN' }),
    [startDate, endDate],
  )

  // 수입 하위 카테고리(급여/환급/이자...) 비중. 기간이 있어야 하는 API라 '전체 기간'에서는 생략
  const incomeRootId = categories.data?.find((c) => c.name === '수입')?.id ?? null
  const breakdown = useApiQuery(
    () =>
      startDate && endDate && categories.data
        ? endpoints.breakdown({ start_date: startDate, end_date: endDate, transaction_type: 'INCOME', parent_id: incomeRootId })
        : Promise.resolve(undefined),
    [startDate, endDate, incomeRootId, categories.data],
  )

  const reloadAll = () => {
    list.reload()
    summary.reload()
    breakdown.reload()
  }

  const setType = async (tx: TransactionOut, type: 'INCOME' | 'TRANSFER') => {
    if (tx.transaction_type === type) return
    setBusyId(tx.id)
    setError(null)
    try {
      await endpoints.updateTransaction(tx.id, { transaction_type: type })
      reloadAll()
    } catch (e) {
      setError(errorDetail(e))
    } finally {
      setBusyId(null)
    }
  }

  const totalPages = list.data ? Math.ceil(list.data.total / PAGE_SIZE) : 0
  const filterTabs: { value: TypeFilter; label: string }[] = [
    { value: '', label: '전체 입금' },
    { value: 'INCOME', label: '수입만' },
    { value: 'TRANSFER', label: '이체만' },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">수입</h1>
        <div className="flex items-center gap-3">
          <MonthNav year={year} month={month} onChange={goMonth} />
          {allTime && <span className="text-xs text-gray-400">전체 기간 표시 중</span>}
          <button
            onClick={() => {
              setAllTime(!allTime)
              setPage(0)
            }}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
          >
            {allTime ? '이 달만' : '전체 기간'}
          </button>
        </div>
      </div>

      {summary.data && (
        <div className="grid gap-4 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-1 lg:grid-cols-2">
            <StatCard
              label="수입 합계"
              value={formatAmount(summary.data.total_income, summary.data.currency)}
              tone={Number(summary.data.total_income) > 0 ? 'positive' : 'default'}
              sub={`${summary.data.income_count}건 · 통계에 포함`}
            />
            <StatCard
              label="이체로 처리된 입금"
              value={formatAmount(summary.data.total_transfer, summary.data.currency)}
              sub={`${summary.data.transfer_count}건 · 통계 미포함`}
            />
          </div>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="mb-3 flex items-baseline justify-between">
              <h2 className="text-sm font-semibold text-gray-700">수입 카테고리별 비중</h2>
              <span className="text-xs text-gray-400">수입 합계 대비</span>
            </div>
            {allTime ? (
              <div className="py-6 text-center text-sm text-gray-400">월을 고르면 카테고리 비중이 보입니다.</div>
            ) : (
              <CategoryBarList items={breakdown.data?.items ?? []} emptyMessage="이 달 수입 내역이 없습니다." />
            )}
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-1 rounded-lg border border-gray-200 bg-white p-1 text-sm">
          {filterTabs.map((t) => (
            <button
              key={t.value}
              onClick={() => {
                setTypeFilter(t.value)
                setPage(0)
              }}
              className={`rounded-md px-3 py-1 ${typeFilter === t.value ? 'bg-gray-900 text-white' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-400">구분을 눌러 수입과 이체를 바로 바꿀 수 있습니다. 이체는 통계에서 빠집니다.</span>
      </div>

      {error && <div className="text-sm text-rose-600">변경하지 못했습니다: {error}</div>}

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="px-4 py-2">날짜</th>
              <th className="px-4 py-2">입금처</th>
              <th className="px-4 py-2 text-right">금액</th>
              <th className="px-4 py-2">카테고리</th>
              <th className="px-4 py-2">계좌</th>
              <th className="px-4 py-2">구분</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {list.data?.items.map((tx) => {
              const transfer = isTransfer(tx.transaction_type)
              return (
                <tr key={tx.id} className="cursor-pointer hover:bg-gray-50" onClick={() => setSelected(tx)}>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-500">{allTime ? tx.transaction_date : formatDate(tx.transaction_date)}</td>
                  <td className="px-4 py-2">
                    <div className="font-medium text-gray-800">{tx.merchant_raw ?? '(알 수 없음)'}</div>
                    {(tx.memo || tx.description) && (
                      <div className="max-w-xs truncate text-xs text-gray-400">{tx.memo || tx.description}</div>
                    )}
                  </td>
                  <td className={`whitespace-nowrap px-4 py-2 text-right tabular-nums ${transfer ? 'text-gray-400' : 'text-emerald-600'}`}>
                    {transfer ? '' : '+'}
                    {formatAmount(tx.amount, tx.currency)}
                  </td>
                  <td className="px-4 py-2 text-gray-600">
                    {tx.category_id ? catNameById.get(tx.category_id) ?? '-' : transfer ? <span className="text-gray-400">-</span> : '미분류'}
                  </td>
                  <td className="px-4 py-2 text-gray-600">{tx.card_id ? cardLabelById.get(tx.card_id) ?? '-' : '-'}</td>
                  <td className="px-4 py-2" onClick={(e) => e.stopPropagation()}>
                    <div className="inline-flex overflow-hidden rounded-md border border-gray-300 text-xs">
                      {(['INCOME', 'TRANSFER'] as const).map((type) => {
                        const active = tx.transaction_type === type
                        return (
                          <button
                            key={type}
                            disabled={busyId === tx.id}
                            onClick={() => setType(tx, type)}
                            className={`px-2.5 py-1 disabled:opacity-50 ${
                              active
                                ? type === 'INCOME'
                                  ? 'bg-emerald-600 text-white'
                                  : 'bg-sky-600 text-white'
                                : 'bg-white text-gray-500 hover:bg-gray-100'
                            }`}
                          >
                            {type === 'INCOME' ? '수입' : '이체'}
                          </button>
                        )
                      })}
                    </div>
                  </td>
                </tr>
              )
            })}
            {list.data && list.data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">이 기간에 들어온 돈이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {list.data && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>총 {list.data.total}건</span>
          <div className="flex items-center gap-2">
            <button disabled={page === 0} onClick={() => setPage((p) => p - 1)} className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40">
              이전
            </button>
            <span>
              {page + 1} / {Math.max(totalPages, 1)}
            </span>
            <button disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)} className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40">
              다음
            </button>
          </div>
        </div>
      )}

      {selected && (
        <TransactionDetailModal
          transaction={selected}
          categories={flatCategories}
          cardLabel={selected.card_id ? cardLabelById.get(selected.card_id) ?? '-' : '-'}
          onClose={() => setSelected(null)}
          onSave={async (update) => {
            await endpoints.updateTransaction(selected.id, update)
            reloadAll()
          }}
        />
      )}
    </div>
  )
}
