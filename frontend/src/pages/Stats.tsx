import { useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { endpoints } from '../api/endpoints'
import type { BreakdownItem } from '../api/types'
import { CategoryDonut, type DonutSlice } from '../components/CategoryDonut'
import { useApiQuery } from '../hooks/useApiQuery'
import { MAX_SLICES, OTHER_COLOR, seriesColor } from '../lib/chartColors'
import { formatAmount, monthRange, toNumber } from '../lib/format'

type PeriodKind = 'month' | 'year'
type TxType = 'EXPENSE' | 'INCOME'

interface Period {
  kind: PeriodKind
  year: number
  month: number // kind === 'year' 일 때는 무시
}

function periodRange(p: Period): [string, string] {
  if (p.kind === 'year') return [`${p.year}-01-01`, `${p.year}-12-31`]
  return monthRange(p.year, p.month)
}

function shiftPeriod(p: Period, delta: number): Period {
  if (p.kind === 'year') return { ...p, year: p.year + delta }
  let y = p.year
  let m = p.month + delta
  if (m === 0) {
    m = 12
    y -= 1
  } else if (m === 13) {
    m = 1
    y += 1
  }
  return { ...p, year: y, month: m }
}

function periodTitle(p: Period): string {
  return p.kind === 'year' ? `${p.year}년` : `${p.year}년 ${p.month}월`
}

function rangeLabel(start: string, end: string): string {
  const fmt = (iso: string) => {
    const [, m, d] = iso.split('-').map(Number)
    return `${m}월 ${d}일`
  }
  return `${fmt(start)} ~ ${fmt(end)}`
}

/** 화면 상태(기간 단위·연월·수입/지출·드릴다운 상위)는 URL 쿼리에 둔다.
 *  뒤로가기로 이전 상태로 돌아갈 수 있고, 특정 달 통계 링크를 그대로 열 수 있다. */
function readState(params: URLSearchParams): { period: Period; txType: TxType; parentId: number | null } {
  const today = new Date()
  const kind: PeriodKind = params.get('period') === 'year' ? 'year' : 'month'
  const year = Number(params.get('year'))
  const month = Number(params.get('month'))
  const parentRaw = params.get('parent')
  return {
    period: {
      kind,
      year: Number.isInteger(year) && year >= 2000 && year <= 2100 ? year : today.getFullYear(),
      month: Number.isInteger(month) && month >= 1 && month <= 12 ? month : today.getMonth() + 1,
    },
    txType: params.get('type') === 'INCOME' ? 'INCOME' : 'EXPENSE',
    parentId: parentRaw && /^\d+$/.test(parentRaw) ? Number(parentRaw) : null,
  }
}

export function Stats() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const { period, txType, parentId } = readState(searchParams)
  const [activeKey, setActiveKey] = useState<string | null>(null)

  const [start, end] = periodRange(period)

  const write = (next: { period: Period; txType: TxType; parentId: number | null }) => {
    const p = new URLSearchParams()
    p.set('period', next.period.kind)
    p.set('year', String(next.period.year))
    if (next.period.kind === 'month') p.set('month', String(next.period.month))
    p.set('type', next.txType)
    if (next.parentId !== null) p.set('parent', String(next.parentId))
    setSearchParams(p)
    setActiveKey(null)
  }
  // 기간/유형이 바뀌면 드릴다운은 최상위로 돌아간다 (다른 달에는 그 상위가 없을 수 있음).
  const changePeriod = (next: Period) => write({ period: next, txType, parentId: null })
  const changeTxType = (next: TxType) => write({ period, txType: next, parentId: null })
  const setParent = (id: number | null) => write({ period, txType, parentId: id })

  const breakdown = useApiQuery(
    () =>
      endpoints.breakdown({
        start_date: start,
        end_date: end,
        transaction_type: txType,
        parent_id: parentId ?? undefined,
      }),
    [start, end, txType, parentId],
  )

  const items: BreakdownItem[] = useMemo(() => breakdown.data?.items ?? [], [breakdown.data])

  // 도넛 조각: 상위 MAX_SLICES 개는 각자, 나머지는 '그 외' 하나로 접는다.
  // 접힌 조각의 금액/비중은 백엔드 값의 단순 합 (표시용, 소수 첫째 자리 반올림 유지).
  const slices: DonutSlice[] = useMemo(() => {
    const head = items.slice(0, MAX_SLICES).map((it, i) => ({
      key: itemKey(it),
      name: it.category,
      value: toNumber(it.amount),
      percentage: it.percentage,
      rank: i,
    }))
    const tail = items.slice(MAX_SLICES)
    if (tail.length === 0) return head
    return [
      ...head,
      {
        key: '__other__',
        name: `그 외 ${tail.length}개`,
        value: tail.reduce((sum, it) => sum + toNumber(it.amount), 0),
        percentage: Math.round(tail.reduce((sum, it) => sum + it.percentage, 0) * 10) / 10,
        rank: MAX_SLICES,
        isOther: true,
      },
    ]
  }, [items])

  const openItem = (item: BreakdownItem) => {
    // 최상위에서 상위 카테고리를 누르면 하위로 드릴다운, 그 외(하위/직접분류/미분류)는 거래내역으로.
    const isParentRow = parentId === null && item.category_id !== null
    if (isParentRow) {
      setParent(item.category_id)
      return
    }
    const params = new URLSearchParams({ start, end, type: txType })
    params.set('category', item.category_id === null ? 'none' : String(item.category_id))
    navigate(`/transactions?${params.toString()}`)
  }

  const data = breakdown.data
  const total = data ? formatAmount(data.total, data.currency) : '-'
  // 드릴다운 중인 상위 카테고리 이름은 응답에서 받는다 (URL에는 id만 있음)
  const parentName = parentId !== null ? data?.parent_name ?? '…' : null

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">통계</h1>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700"
            value={period.kind}
            onChange={(e) => changePeriod({ ...period, kind: e.target.value as PeriodKind })}
            aria-label="기간 단위"
          >
            <option value="month">월간</option>
            <option value="year">연간</option>
          </select>
          <button
            onClick={() => changePeriod(shiftPeriod(period, -1))}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
            aria-label="이전 기간"
          >
            ‹
          </button>
          <div className="w-40 text-center">
            <div className="text-base font-semibold leading-tight">{periodTitle(period)}</div>
            <div className="text-xs text-gray-400">{rangeLabel(start, end)}</div>
          </div>
          <button
            onClick={() => changePeriod(shiftPeriod(period, 1))}
            className="rounded-md border border-gray-300 px-2 py-1 text-sm text-gray-600 hover:bg-gray-100"
            aria-label="다음 기간"
          >
            ›
          </button>
        </div>
      </div>

      {breakdown.error && <div className="text-sm text-rose-600">데이터를 불러오지 못했습니다: {breakdown.error}</div>}

      <div className="rounded-lg border border-gray-200 bg-white">
        {/* 수입 / 지출 토글 - 두 총액을 함께 보여 주고 선택된 쪽을 분석한다 */}
        <div className="grid grid-cols-2 border-b border-gray-100" role="radiogroup" aria-label="수입/지출 선택">
          {(
            [
              ['INCOME', '수입', data?.total_income],
              ['EXPENSE', '지출', data?.total_expense],
            ] as const
          ).map(([kind, label, amount]) => {
            const selected = txType === kind
            return (
              <button
                key={kind}
                role="radio"
                aria-checked={selected}
                onClick={() => changeTxType(kind)}
                className={`flex items-center justify-center gap-2 py-3 text-sm transition-colors ${
                  selected ? 'font-semibold text-gray-900' : 'text-gray-400 hover:text-gray-600'
                }`}
              >
                <span
                  className={`inline-flex h-4 w-4 items-center justify-center rounded-full border ${
                    selected ? 'border-emerald-500' : 'border-gray-300'
                  }`}
                >
                  {selected && <span className="h-2 w-2 rounded-full bg-emerald-500" />}
                </span>
                {label}
                <span className={`tabular-nums ${selected ? (kind === 'INCOME' ? 'text-sky-600' : 'text-emerald-600') : ''}`}>
                  {amount !== undefined && data ? formatAmount(amount, data.currency) : '-'}
                </span>
              </button>
            )
          })}
        </div>

        <div className="grid gap-6 p-6 md:grid-cols-[auto_minmax(0,1fr)] md:items-start">
          <div className="flex flex-col items-center gap-3">
            <CategoryDonut
              slices={slices}
              activeKey={activeKey}
              onActiveChange={setActiveKey}
              emptyLabel={`${txType === 'INCOME' ? '수입' : '지출'} 없음`}
            />
            {parentId !== null && (
              <button
                onClick={() => setParent(null)}
                className="rounded-md border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100"
              >
                ‹ 전체 카테고리로
              </button>
            )}
          </div>

          <div className="min-w-0">
            <div className="flex items-baseline justify-between border-b border-gray-200 pb-3">
              <span className="text-sm text-gray-500">
                {parentName !== null ? (
                  <>
                    <span className="font-medium text-gray-700">{parentName}</span> 하위
                  </>
                ) : (
                  '전체'
                )}
                {data && <span className="ml-2 text-xs text-gray-400">{data.count}건</span>}
              </span>
              <span className="text-base font-semibold tabular-nums text-gray-700">{total}</span>
            </div>

            {breakdown.loading && items.length === 0 ? (
              <div className="py-10 text-center text-sm text-gray-400">불러오는 중…</div>
            ) : items.length === 0 ? (
              <div className="py-10 text-center text-sm text-gray-400">
                이 기간에는 {txType === 'INCOME' ? '수입' : '지출'} 내역이 없습니다.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {items.map((item, i) => {
                  const key = itemKey(item)
                  const color = i < MAX_SLICES ? seriesColor(i) : OTHER_COLOR
                  const highlighted = activeKey === key || (activeKey === '__other__' && i >= MAX_SLICES)
                  const drillsDown = parentId === null && item.category_id !== null
                  return (
                    <li key={key}>
                      <button
                        onClick={() => openItem(item)}
                        onMouseEnter={() => setActiveKey(i < MAX_SLICES ? key : '__other__')}
                        onMouseLeave={() => setActiveKey(null)}
                        className={`flex w-full items-center gap-3 px-1 py-3 text-left text-sm transition-colors hover:bg-gray-50 ${
                          highlighted ? 'bg-gray-50' : ''
                        }`}
                        title={drillsDown ? '하위 카테고리 보기' : '거래내역 보기'}
                      >
                        <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} aria-hidden />
                        <span className="min-w-0 flex-1 truncate">
                          <span className="font-medium text-gray-800">{item.category}</span>
                          <span className="ml-1.5 tabular-nums text-gray-400">{item.percentage}%</span>
                        </span>
                        <span className="tabular-nums font-semibold text-gray-900">
                          {formatAmount(item.amount, data?.currency ?? 'KRW')}
                        </span>
                        <span className="text-gray-300" aria-hidden>
                          ›
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </div>
      </div>

      <p className="text-xs text-gray-400">
        이체와 통계 제외 거래는 수입·지출 어디에도 포함되지 않습니다. 비중은 선택한 쪽(수입 또는 지출)의 합계 대비이며, 상위
        카테고리를 누르면 하위 카테고리별로, 하위 카테고리를 누르면 해당 거래내역으로 이동합니다.
      </p>
    </div>
  )
}

function itemKey(item: BreakdownItem): string {
  return `${item.category_id ?? 'none'}:${item.category}`
}
