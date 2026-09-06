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

export function isTransfer(transactionType: string): boolean {
  return transactionType === 'TRANSFER'
}

/** 해당 월의 [첫날, 마지막날] ISO 날짜. */
export function monthRange(year: number, month: number): [string, string] {
  const mm = String(month).padStart(2, '0')
  const lastDay = new Date(year, month, 0).getDate()
  return [`${year}-${mm}-01`, `${year}-${mm}-${String(lastDay).padStart(2, '0')}`]
}
