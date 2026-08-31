import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { endpoints } from '../api/endpoints'
import type { TransactionOut } from '../api/types'
import { TransactionDetailModal } from '../components/TransactionDetailModal'
import { useApiQuery } from '../hooks/useApiQuery'
import { categoryNameMap, flattenCategories } from '../lib/categoryTree'
import { formatAmount, formatDate } from '../lib/format'

const PAGE_SIZE = 30

export function Transactions() {
  const [searchParams] = useSearchParams()
  const highlightId = searchParams.get('highlight')

  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [minAmount, setMinAmount] = useState('')
  const [maxAmount, setMaxAmount] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [cardId, setCardId] = useState('')
  const [transactionType, setTransactionType] = useState('')
  const [q, setQ] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'amount'>('date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(0)
  const [selected, setSelected] = useState<TransactionOut | null>(null)

  const categories = useApiQuery(() => endpoints.categories(), [])
  const cards = useApiQuery(() => endpoints.cards(), [])
  const flatCategories = useMemo(() => (categories.data ? flattenCategories(categories.data) : []), [categories.data])
  const catNameById = useMemo(() => (categories.data ? categoryNameMap(categories.data) : new Map()), [categories.data])
  const cardLabelById = useMemo(() => {
    const map = new Map<number, string>()
    for (const c of cards.data ?? []) map.set(c.id, `${c.institution} ${c.card_number_masked ?? ''}`.trim())
    return map
  }, [cards.data])

  const list = useApiQuery(
    () =>
      endpoints.transactions({
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        min_amount: minAmount ? Number(minAmount) : undefined,
        max_amount: maxAmount ? Number(maxAmount) : undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
        card_id: cardId ? Number(cardId) : undefined,
        transaction_type: transactionType || undefined,
        q: q || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    [startDate, endDate, minAmount, maxAmount, categoryId, cardId, transactionType, q, sortBy, sortDir, page],
  )

  const openTransaction = async (tx: TransactionOut) => {
    setSelected(tx)
  }

  useMemo(() => {
    if (highlightId && list.data) {
      const found = list.data.items.find((t) => t.id === Number(highlightId))
      if (found) setSelected(found)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightId, list.data])

  const toggleSort = (field: 'date' | 'amount') => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortDir('desc')
    }
    setPage(0)
  }

  const resetPage = <T,>(setter: (v: T) => void) => (v: T) => {
    setter(v)
    setPage(0)
  }

  const totalPages = list.data ? Math.ceil(list.data.total / PAGE_SIZE) : 0

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">거래내역</h1>

      <div className="flex flex-col gap-3 rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-gray-500">기간</span>
          <input type="date" className="rounded-md border border-gray-300 px-2 py-1" value={startDate} onChange={(e) => resetPage(setStartDate)(e.target.value)} />
          <span className="text-gray-400">~</span>
          <input type="date" className="rounded-md border border-gray-300 px-2 py-1" value={endDate} onChange={(e) => resetPage(setEndDate)(e.target.value)} />

          <span className="ml-4 text-gray-500">금액</span>
          <input type="number" placeholder="최소" className="w-24 rounded-md border border-gray-300 px-2 py-1" value={minAmount} onChange={(e) => resetPage(setMinAmount)(e.target.value)} />
          <span className="text-gray-400">~</span>
          <input type="number" placeholder="최대" className="w-24 rounded-md border border-gray-300 px-2 py-1" value={maxAmount} onChange={(e) => resetPage(setMaxAmount)(e.target.value)} />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-sm">
          <select className="rounded-md border border-gray-300 px-2 py-1" value={categoryId} onChange={(e) => resetPage(setCategoryId)(e.target.value)}>
            <option value="">카테고리 전체</option>
            {flatCategories.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>

          <select className="rounded-md border border-gray-300 px-2 py-1" value={cardId} onChange={(e) => resetPage(setCardId)(e.target.value)}>
            <option value="">결제수단 전체</option>
            {(cards.data ?? []).map((c) => (
              <option key={c.id} value={c.id}>{c.institution} {c.card_number_masked}</option>
            ))}
          </select>

          <select className="rounded-md border border-gray-300 px-2 py-1" value={transactionType} onChange={(e) => resetPage(setTransactionType)(e.target.value)}>
            <option value="">수입/지출 전체</option>
            <option value="EXPENSE">지출</option>
            <option value="INCOME">수입</option>
            <option value="TRANSFER">이체</option>
          </select>

          <input
            type="text"
            placeholder="🔍 가맹점/내용 검색"
            className="min-w-[200px] flex-1 rounded-md border border-gray-300 px-3 py-1"
            value={q}
            onChange={(e) => resetPage(setQ)(e.target.value)}
          />
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-left text-gray-500">
            <tr>
              <th className="cursor-pointer select-none px-4 py-2" onClick={() => toggleSort('date')}>
                날짜 {sortBy === 'date' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-2">가맹점</th>
              <th className="cursor-pointer select-none px-4 py-2 text-right" onClick={() => toggleSort('amount')}>
                금액 {sortBy === 'amount' && (sortDir === 'asc' ? '↑' : '↓')}
              </th>
              <th className="px-4 py-2">카테고리</th>
              <th className="px-4 py-2">결제수단</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {list.data?.items.map((tx) => (
              <tr key={tx.id} className="cursor-pointer hover:bg-gray-50" onClick={() => openTransaction(tx)}>
                <td className="px-4 py-2 text-gray-500">{formatDate(tx.transaction_date)}</td>
                <td className="px-4 py-2 font-medium text-gray-800">
                  {tx.merchant_raw ?? '(알 수 없음)'}
                  {tx.is_excluded && <span className="ml-2 rounded bg-amber-50 px-1.5 py-0.5 text-xs text-amber-600">취소</span>}
                </td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {tx.transaction_type === 'INCOME' ? '+' : '-'}
                  {formatAmount(tx.amount, tx.currency)}
                </td>
                <td className="px-4 py-2 text-gray-600">{tx.category_id ? catNameById.get(tx.category_id) ?? '-' : '미분류'}</td>
                <td className="px-4 py-2 text-gray-600">{tx.card_id ? cardLabelById.get(tx.card_id) ?? '-' : '-'}</td>
              </tr>
            ))}
            {list.data && list.data.items.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">조건에 맞는 거래가 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {list.data && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>총 {list.data.total}건</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
            >
              이전
            </button>
            <span>{page + 1} / {Math.max(totalPages, 1)}</span>
            <button
              disabled={page + 1 >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-md border border-gray-300 px-3 py-1 disabled:opacity-40"
            >
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
          onSave={async (catId, memo) => {
            await endpoints.updateTransaction(selected.id, { category_id: catId, memo })
            list.reload()
          }}
        />
      )}
    </div>
  )
}
