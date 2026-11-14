import { useState } from 'react'
import { endpoints } from '../api/endpoints'
import type { CardOut } from '../api/types'
import { useApiQuery } from '../hooks/useApiQuery'

const TYPE_LABEL: Record<string, string> = { CREDIT: '카드', BANK: '계좌', PREPAID: '선불' }

/** 결제수단 별칭 편집. 별칭은 모든 표의 결제수단 칸에 그대로 쓰인다. */
export function CardNicknames() {
  const cards = useApiQuery(() => endpoints.cards(), [])
  const [editing, setEditing] = useState<{ id: number; value: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const save = async (card: CardOut) => {
    if (!editing || editing.id !== card.id) return
    setError(null)
    try {
      await endpoints.updateCard(card.id, editing.value)
      setEditing(null)
      cards.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-gray-700">결제수단 이름</h2>
        <span className="text-xs text-gray-400">가져온 파일에서 자동으로 만들어집니다. 이름을 누르면 바꿀 수 있습니다.</span>
      </div>
      {error && <div className="mb-2 text-sm text-rose-600">저장하지 못했습니다: {error}</div>}
      <table className="w-full text-sm">
        <thead className="border-b border-gray-200 text-left text-gray-500">
          <tr>
            <th className="py-2 pr-4">표시 이름</th>
            <th className="py-2 pr-4">기관</th>
            <th className="py-2 pr-4">번호</th>
            <th className="py-2">종류</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {(cards.data ?? []).map((card) => (
            <tr key={card.id}>
              <td className="py-1.5 pr-4">
                {editing?.id === card.id ? (
                  <input
                    autoFocus
                    className="w-48 rounded-md border border-gray-300 px-2 py-1"
                    value={editing.value}
                    onChange={(e) => setEditing({ id: card.id, value: e.target.value })}
                    onBlur={() => save(card)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') save(card)
                      if (e.key === 'Escape') setEditing(null)
                    }}
                  />
                ) : (
                  <button
                    onClick={() => setEditing({ id: card.id, value: card.card_name ?? '' })}
                    className="rounded px-1 font-medium text-gray-800 hover:bg-gray-100"
                    title="클릭해서 이름 바꾸기"
                  >
                    {card.card_name || <span className="font-normal text-gray-400">(별칭 없음)</span>}
                  </button>
                )}
              </td>
              <td className="py-1.5 pr-4 text-gray-600">{card.institution}</td>
              <td className="py-1.5 pr-4 text-gray-400">{card.card_number_masked}</td>
              <td className="py-1.5 text-gray-400">{TYPE_LABEL[card.card_type ?? ''] ?? card.card_type ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
