import { useState } from 'react'
import type { SpendingAnomalies } from '../api/types'
import { formatAmount, formatMonthLabel, formatPercent } from '../lib/format'

interface Props {
  year: number
  month: number
  anomalies: SpendingAnomalies | undefined
  loading: boolean
}

function suggestedQuestions(year: number, month: number): string[] {
  const label = formatMonthLabel(year, month)
  return [
    `${label} 소비 패턴을 분석해줘.`,
    `지난달보다 ${label}에 무엇을 더 많이 썼어?`,
    `${label}에 평소보다 많이 쓴 항목을 찾아줘.`,
    `매달 반복적으로 나가는 비용을 찾아줘.`,
    `내 소비에서 줄이기 쉬운 항목을 찾아줘.`,
  ]
}

function AskChip({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard API unavailable (e.g. insecure context) - silently ignore, chip text is still visible to copy manually
    }
  }

  return (
    <button
      onClick={copy}
      className="rounded-full border border-gray-300 bg-white px-3 py-1.5 text-left text-xs text-gray-700 hover:border-gray-400 hover:bg-gray-50"
      title="클릭하면 클립보드에 복사됩니다 - Claude 채팅에 붙여넣어 물어보세요"
    >
      {copied ? '복사됨! Claude에 붙여넣으세요' : `“${text}”`}
    </button>
  )
}

export function AiAnalysisPanel({ year, month, anomalies, loading }: Props) {
  if (loading || !anomalies) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-semibold text-gray-700">🤖 AI 소비 분석</h2>
        <div className="py-4 text-center text-sm text-gray-400">불러오는 중...</div>
      </div>
    )
  }

  const { overall, categories } = anomalies
  const topCategories = categories.slice(0, 3)
  const hasBaseline = overall.change_percentage !== null

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-gray-700">🤖 AI 소비 분석</h2>

      <div className="mb-4 space-y-1.5 text-sm text-gray-700">
        {hasBaseline ? (
          <p>
            이번 달 지출은 <span className="font-semibold">{formatAmount(overall.current_total)}</span>으로, 최근{' '}
            {anomalies.lookback_months}개월 평균보다{' '}
            <span className={overall.change_percentage! >= 0 ? 'font-semibold text-rose-600' : 'font-semibold text-emerald-600'}>
              {formatPercent(overall.change_percentage)}
            </span>{' '}
            {overall.change_percentage! >= 0 ? '많습니다' : '적습니다'}.
          </p>
        ) : (
          <p>최근 {anomalies.lookback_months}개월치 데이터가 아직 없어 평균 대비 비교는 어렵습니다.</p>
        )}

        {topCategories.length > 0 && (
          <ul className="list-inside list-disc space-y-1 text-gray-600">
            {topCategories.map((c) => (
              <li key={c.category}>
                <span className="font-medium text-gray-800">{c.category}</span>
                {c.is_new ? (
                  <> 이(가) 새로 지출되었습니다 ({formatAmount(c.current_amount)})</>
                ) : (
                  <>
                    {' '}
                    {formatPercent(c.change_percentage)} 변동 ({formatAmount(c.baseline_average)} → {formatAmount(c.current_amount)})
                  </>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="border-t border-gray-100 pt-3">
        <div className="mb-2 text-xs text-gray-400">
          이 앱은 API 키 없이 동작합니다 - 아래 질문을 눌러 복사한 뒤, my-ledger MCP가 연결된 Claude 채팅에 붙여넣어 물어보세요.
        </div>
        <div className="flex flex-wrap gap-2">
          {suggestedQuestions(year, month).map((q) => (
            <AskChip key={q} text={q} />
          ))}
        </div>
      </div>
    </div>
  )
}
