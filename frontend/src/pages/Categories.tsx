import { useMemo, useState } from 'react'
import { endpoints } from '../api/endpoints'
import type { CategoryRuleOut } from '../api/types'
import { useApiQuery } from '../hooks/useApiQuery'
import { flattenCategories } from '../lib/categoryTree'

export function Categories() {
  const categories = useApiQuery(() => endpoints.categories(), [])
  const rules = useApiQuery(() => endpoints.categoryRules(), [])
  const flatCategories = useMemo(() => (categories.data ? flattenCategories(categories.data) : []), [categories.data])
  const categoryLabelById = useMemo(() => {
    const map = new Map<number, string>()
    for (const c of flatCategories) map.set(c.id, c.label)
    return map
  }, [flatCategories])

  const [newKeyword, setNewKeyword] = useState('')
  const [newCategoryId, setNewCategoryId] = useState('')
  const [newPriority, setNewPriority] = useState('10')
  const [adding, setAdding] = useState(false)

  const addRule = async () => {
    if (!newKeyword.trim() || !newCategoryId) return
    setAdding(true)
    try {
      await endpoints.createCategoryRule({
        keyword: newKeyword.trim(),
        category_id: Number(newCategoryId),
        priority: Number(newPriority) || 0,
      })
      setNewKeyword('')
      rules.reload()
    } finally {
      setAdding(false)
    }
  }

  const toggleEnabled = async (rule: CategoryRuleOut) => {
    await endpoints.updateCategoryRule(rule.id, { enabled: !rule.enabled })
    rules.reload()
  }

  const removeRule = async (rule: CategoryRuleOut) => {
    await endpoints.deleteCategoryRule(rule.id)
    rules.reload()
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">카테고리</h1>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-700">카테고리 구조</h2>
        <div className="grid grid-cols-3 gap-4">
          {categories.data?.map((top) => (
            <div key={top.id}>
              <div className="font-medium text-gray-800">{top.name}</div>
              {top.children.length > 0 && (
                <ul className="mt-1 space-y-0.5 pl-3 text-sm text-gray-500">
                  {top.children.map((child) => (
                    <li key={child.id}>└ {child.name}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h2 className="mb-3 text-sm font-semibold text-gray-700">자동 분류 Rule</h2>

        <div className="mb-4 flex flex-wrap items-center gap-2 rounded-md bg-gray-50 p-3 text-sm">
          <input
            type="text"
            placeholder="키워드 (예: 스타벅스)"
            className="rounded-md border border-gray-300 px-3 py-1.5"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
          />
          <select
            className="rounded-md border border-gray-300 px-3 py-1.5"
            value={newCategoryId}
            onChange={(e) => setNewCategoryId(e.target.value)}
          >
            <option value="">카테고리 선택</option>
            {flatCategories.map((c) => (
              <option key={c.id} value={c.id}>{c.label}</option>
            ))}
          </select>
          <input
            type="number"
            className="w-20 rounded-md border border-gray-300 px-3 py-1.5"
            value={newPriority}
            onChange={(e) => setNewPriority(e.target.value)}
            title="우선순위"
          />
          <button
            onClick={addRule}
            disabled={adding || !newKeyword.trim() || !newCategoryId}
            className="rounded-md bg-gray-900 px-4 py-1.5 text-white disabled:opacity-40"
          >
            추가
          </button>
        </div>

        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 text-left text-gray-500">
            <tr>
              <th className="py-2 pr-4">키워드</th>
              <th className="py-2 pr-4">카테고리</th>
              <th className="py-2 pr-4 text-right">우선순위</th>
              <th className="py-2 pr-4">출처</th>
              <th className="py-2 pr-4">사용</th>
              <th className="py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {rules.data?.map((rule) => (
              <tr key={rule.id} className={!rule.enabled ? 'opacity-40' : ''}>
                <td className="py-2 pr-4 font-medium text-gray-800">{rule.keyword}</td>
                <td className="py-2 pr-4 text-gray-600">{categoryLabelById.get(rule.category_id) ?? rule.category_id}</td>
                <td className="py-2 pr-4 text-right tabular-nums text-gray-600">{rule.priority}</td>
                <td className="py-2 pr-4 text-gray-400">{rule.source === 'USER' ? '사용자' : '기본'}</td>
                <td className="py-2 pr-4">
                  <input type="checkbox" checked={rule.enabled} onChange={() => toggleEnabled(rule)} />
                </td>
                <td className="py-2 text-right">
                  <button onClick={() => removeRule(rule)} className="text-gray-400 hover:text-rose-600">
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
