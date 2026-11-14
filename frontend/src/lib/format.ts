// Formatting only - every number here already comes computed from the
// backend (see design doc 8.9). This file never sums, averages, or
// derives a percentage; it only turns a value into a display string.

export function toNumber(value: string | number): number {
  return typeof value === 'number' ? value : parseFloat(value)
}

const krwFormatter = new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 })
const usdFormatter = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function formatAmount(value: string | number, currency = 'KRW'): string {
  const n = toNumber(value)
  const formatted = currency === 'KRW' ? krwFormatter.format(n) : usdFormatter.format(n)
  const symbol = currency === 'KRW' ? '원' : ` ${currency}`
  return `${formatted}${symbol}`
}

export function formatSigned(value: string | number, currency = 'KRW'): string {
  const n = toNumber(value)
  const sign = n > 0 ? '+' : ''
  return `${sign}${formatAmount(n, currency)}`
}

export function formatDate(isoDate: string): string {
  const [, month, day] = isoDate.split('-')
  return `${month}/${day}`
}

export function formatMonthLabel(year: number, month: number): string {
  return `${year}년 ${month}월`
}

/** 결제수단 표시 이름: 별칭이 있으면 별칭, 없으면 기관명 + 마스킹 번호 */
export function cardLabel(card: { institution: string; card_number_masked: string | null; card_name?: string | null }): string {
  return card.card_name || `${card.institution} ${card.card_number_masked ?? ''}`.trim()
}

/** 금액 글자색: 수입은 초록, 이체는 회색, 지출은 기본 - 모든 표에서 같은 규칙 */
export function amountColorClass(transactionType: string): string {
  if (transactionType === 'INCOME') return 'text-emerald-600'
  if (transactionType === 'TRANSFER') return 'text-gray-400'
  return 'text-gray-900'
}

export function formatPercent(value: number | null): string {
  if (value === null) return '-'
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}

/** 금액 앞 부호. 이체(TRANSFER)는 지출도 수입도 아니므로 부호를 붙이지 않는다. */
export function amountSign(transactionType: string): string {
  if (transactionType === 'INCOME') return '+'
  if (transactionType === 'TRANSFER') return ''
  return '-'
}

/** 바꿀 수 있는 거래 구분 - 들어온 돈은 수입/이체, 나간 돈은 지출/이체 */
export function typeOptionsFor(direction: 'IN' | 'OUT'): { value: 'INCOME' | 'EXPENSE' | 'TRANSFER'; label: string }[] {
  return direction === 'IN'
    ? [
        { value: 'INCOME', label: '수입' },
        { value: 'TRANSFER', label: '이체' },
      ]
    : [
        { value: 'EXPENSE', label: '지출' },
        { value: 'TRANSFER', label: '이체' },
      ]
}

export function isTransfer(transactionType: string): boolean {
  return transactionType === 'TRANSFER'
}

/** 해당 월의 [첫날, 마지막날] ISO 날짜. */
export function monthRange(year: number, month: number): [string, string] {
  const mm = String(month).padStart(2, '0')
  const lastDay = new Date(year, month, 0).getDate()
  return [`${year}-${mm}-01`, `${year}-${mm}-${String(lastDay).padStart(2, '0')}`]
}
