import type { CategoryOut } from '../api/types'

export interface FlatCategory {
  id: number
  label: string // e.g. "식비 > 카페" or "쇼핑" for a top-level-only category
}

export function flattenCategories(tree: CategoryOut[]): FlatCategory[] {
  const result: FlatCategory[] = []
  for (const top of tree) {
    if (top.children.length === 0) {
      result.push({ id: top.id, label: top.name })
    } else {
      // A parent with children is itself a valid target (e.g. 규칙이
      // 세부 분류 없이 상위 '교통'으로 분류하는 경우) - 빼면 규칙
      // 목록에서 라벨을 못 찾아 raw id가 노출된다.
      result.push({ id: top.id, label: `${top.name} (전체)` })
      for (const child of top.children) {
        result.push({ id: child.id, label: `${top.name} > ${child.name}` })
      }
    }
  }
  return result
}

export function categoryNameMap(tree: CategoryOut[]): Map<number, string> {
  const map = new Map<number, string>()
  for (const top of tree) {
    map.set(top.id, top.name)
    for (const child of top.children) map.set(child.id, child.name)
  }
  return map
}
