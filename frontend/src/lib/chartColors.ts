// 통계 도넛/목록에서 쓰는 카테고리 색. 순위(큰 금액부터)대로 고정 슬롯을 배정하고,
// 슬롯을 넘는 항목은 회색 '그 외'로 접는다 (색을 새로 만들어 돌려 쓰지 않음).
// 팔레트는 dataviz 검증 스크립트를 통과한 조합 (인접 색 CVD ΔE >= 8, 정상 시각 ΔE >= 15).
export const SERIES_COLORS = ['#14a389', '#2a78d6', '#eb6834', '#7a4fd6', '#e87ba4', '#eda100', '#5a9a2b'] as const
export const OTHER_COLOR = '#9ca3af'
export const MAX_SLICES = SERIES_COLORS.length

export function seriesColor(rank: number): string {
  return rank < MAX_SLICES ? SERIES_COLORS[rank] : OTHER_COLOR
}
