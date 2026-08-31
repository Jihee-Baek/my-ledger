import { Link } from 'react-router-dom'
import { formatAmount, formatDate } from '../lib/format'
import type { TransactionOut } from '../api/types'

export function RecentTransactions({ items }: { items: TransactionOut[] }) {
  if (items.length === 0) {
    return <div className="py-6 text-center text-sm text-gray-400">최근 거래가 없습니다.</div>
  }

  return (
    <div className="flex flex-col divide-y divide-gray-100">
      {items.map((tx) => (
        <Link
          key={tx.id}
          to={`/transactions?highlight=${tx.id}`}
          className="flex items-center justify-between py-2.5 text-sm hover:bg-gray-50"
        >
          <div className="flex items-center gap-3">
            <span className="w-10 shrink-0 text-gray-400">{formatDate(tx.transaction_date)}</span>
            <span className="font-medium text-gray-800">{tx.merchant_raw ?? '(알 수 없음)'}</span>
          </div>
          <span className={tx.transaction_type === 'INCOME' ? 'text-emerald-600' : 'text-gray-900'}>
            {tx.transaction_type === 'INCOME' ? '+' : '-'}
            {formatAmount(tx.amount, tx.currency)}
          </span>
        </Link>
      ))}
    </div>
  )
}
