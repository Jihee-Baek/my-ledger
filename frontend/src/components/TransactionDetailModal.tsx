import { useState } from 'react'
import type { TransactionOut } from '../api/types'
import type { FlatCategory } from '../lib/categoryTree'
import type { TransactionUpdate } from '../api/types'
import { amountSign, formatAmount, isTransfer, typeOptionsFor } from '../lib/format'

/** FastAPI 에러 본문 {"detail": "..."} 에서 사람이 읽을 메시지만 꺼낸다 */
export function errorDetail(e: unknown): string {
  const msg = e instanceof Error ? e.message : String(e)
  try {
    const detail = JSON.parse(msg)?.detail
    return typeof detail === 'string' ? detail : msg
  } catch {
    return msg
  }
}

interface Props {
  transaction: TransactionOut
  categories: FlatCategory[]
  cardLabel: string
  onClose: () => void
  onSave: (update: TransactionUpdate) => Promise<void>
}

export function TransactionDetailModal({ transaction, categories, cardLabel, onClose, onSave }: Props) {
  const [categoryId, setCategoryId] = useState<number | null>(transaction.category_id)
  const [memo, setMemo] = useState(transaction.memo ?? '')
  const [txType, setTxType] = useState(transaction.transaction_type)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const typeChanged = txType !== transaction.transaction_type

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await onSave({
        ...(typeChanged ? { transaction_type: txType } : {}),
        // 이체는 분류 대상이 아님. 구분을 바꿨는데 카테고리를 건드리지 않았으면 서버가 다시 분류한다.
        category_id: isTransfer(txType) || (typeChanged && categoryId === transaction.category_id) ? null : categoryId,
        memo,
      })
      onClose()
    } catch (e) {
      setError(errorDetail(e))
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
            {amountSign(transaction.transaction_type)}
            {formatAmount(transaction.amount, transaction.currency)}
          </dd>
          <dt className="text-gray-500">결제수단</dt>
          <dd>{cardLabel}</dd>
          {transaction.is_excluded && (
            <>
              <dt className="text-gray-500">상태</dt>
              <dd className="text-amber-600">통계에서 제외된 거래 (취소 또는 다른 내역과 중복)</dd>
            </>
          )}
          {isTransfer(transaction.transaction_type) && (
            <>
              <dt className="text-gray-500">상태</dt>
              <dd className="text-sky-600">이체 - 자금 이동이라 수입/지출 통계에 포함되지 않음</dd>
            </>
          )}
        </dl>

        <label className="mb-1 block text-sm font-medium text-gray-700">
          구분 <span className="font-normal text-gray-400">({transaction.direction === 'IN' ? '들어온 돈' : '나간 돈'})</span>
        </label>
        <div className="mb-4 flex gap-2">
          {typeOptionsFor(transaction.direction).map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setTxType(opt.value)}
              className={`flex-1 rounded-md border px-3 py-2 text-sm ${
                txType === opt.value ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-300 text-gray-600 hover:bg-gray-50'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        {typeChanged && (
          <p className="-mt-2 mb-4 text-xs text-gray-500">
            {isTransfer(txType)
              ? '이체로 바꾸면 수입/지출 통계에서 빠지고 카테고리가 비워집니다.'
              : '저장하면 카테고리를 자동으로 다시 분류합니다. 직접 고르면 그 값이 우선합니다.'}
          </p>
        )}

        <label className="mb-1 block text-sm font-medium text-gray-700">카테고리</label>
        <select
          className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-400"
          disabled={isTransfer(txType)}
          value={isTransfer(txType) ? '' : categoryId ?? ''}
          onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">{isTransfer(txType) ? '이체 (분류 불필요)' : '미분류'}</option>
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

        {error && <p className="mb-3 text-sm text-rose-600">{error}</p>}

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
