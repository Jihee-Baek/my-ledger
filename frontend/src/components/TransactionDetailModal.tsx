import { useState } from 'react'
import type { TransactionOut } from '../api/types'
import type { FlatCategory } from '../lib/categoryTree'
import { formatAmount } from '../lib/format'

interface Props {
  transaction: TransactionOut
  categories: FlatCategory[]
  cardLabel: string
  onClose: () => void
  onSave: (categoryId: number | null, memo: string) => Promise<void>
}

export function TransactionDetailModal({ transaction, categories, cardLabel, onClose, onSave }: Props) {
  const [categoryId, setCategoryId] = useState<number | null>(transaction.category_id)
  const [memo, setMemo] = useState(transaction.memo ?? '')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave(categoryId, memo)
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-semibold">{transaction.merchant_raw ?? '(알 수 없음)'}</h2>

        <dl className="mb-5 grid grid-cols-[80px_1fr] gap-y-2 text-sm">
          <dt className="text-gray-500">날짜</dt>
          <dd>
            {transaction.transaction_date}
            {transaction.transaction_time && (
              <span className="ml-2 text-gray-500">{transaction.transaction_time.slice(0, 5)}</span>
            )}
          </dd>
          <dt className="text-gray-500">금액</dt>
          <dd className="tabular-nums">
            {transaction.transaction_type === 'INCOME' ? '+' : '-'}
            {formatAmount(transaction.amount, transaction.currency)}
          </dd>
          <dt className="text-gray-500">결제수단</dt>
          <dd>{cardLabel}</dd>
          {transaction.is_excluded && (
            <>
              <dt className="text-gray-500">상태</dt>
              <dd className="text-amber-600">취소된 거래 (통계에서 제외)</dd>
            </>
          )}
        </dl>

        <label className="mb-1 block text-sm font-medium text-gray-700">카테고리</label>
        <select
          className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          value={categoryId ?? ''}
          onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">미분류</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>

        <label className="mb-1 block text-sm font-medium text-gray-700">메모</label>
        <textarea
          className="mb-5 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          rows={2}
          value={memo}
          onChange={(e) => setMemo(e.target.value)}
        />

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-800 disabled:opacity-50"
          >
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>
    </div>
  )
}
