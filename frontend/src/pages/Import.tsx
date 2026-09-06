import { useRef, useState } from 'react'
import { endpoints } from '../api/endpoints'
import { ApiError } from '../api/client'
import type { ImportResultOut } from '../api/types'

const SOURCE_LABEL: Record<string, string> = {
  samsung_card: '삼성카드',
  shinhan_card: '신한카드',
  hyundai_card: '현대카드',
}

export function Import() {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ImportResultOut | null>(null)
  const [result, setResult] = useState<ImportResultOut | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const reset = () => {
    setFile(null)
    setPreview(null)
    setResult(null)
    setError(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  const handleFile = async (f: File) => {
    setFile(f)
    setResult(null)
    setError(null)
    setLoading(true)
    try {
      const res = await endpoints.importFile(f, true)
      setPreview(res)
    } catch (err) {
      setPreview(null)
      setError(err instanceof ApiError ? err.message : '미리보기 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const runImport = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await endpoints.importFile(file, false)
      setResult(res)
      setPreview(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '가져오기 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">거래내역 가져오기</h1>

      {!result && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <label className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 px-6 py-10 text-gray-500 hover:border-gray-400 hover:bg-gray-50">
            <span className="text-3xl">📄</span>
            <span>{file ? file.name : '카드사·은행 다운로드 파일을 선택하세요 (xlsx / xls / pdf / csv)'}</span>
            <span className="rounded-md bg-gray-900 px-4 py-1.5 text-sm text-white">파일 선택</span>
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls,.csv,.pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) handleFile(f)
              }}
            />
          </label>

          {loading && <div className="mt-4 text-center text-sm text-gray-400">처리 중...</div>}
          {error && <div className="mt-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-600">{error}</div>}

          {preview && !loading && (
            <div className="mt-5 rounded-lg border border-gray-200 p-4">
              <div className="mb-3 text-sm text-gray-500">
                자동 감지된 금융기관: <span className="font-medium text-gray-800">{SOURCE_LABEL[preview.source] ?? preview.source}</span>
              </div>
              <div className="grid grid-cols-5 gap-3 text-center text-sm">
                <Stat label="전체" value={preview.total} />
                <Stat label="신규" value={preview.imported} tone="positive" />
                <Stat label="중복" value={preview.duplicates} tone="muted" />
                <Stat label="분류 완료" value={preview.classified} tone="positive" />
                <Stat label="미분류" value={preview.unclassified} tone="warning" />
              </div>
              <div className="mt-5 flex justify-end gap-2">
                <button onClick={reset} className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
                  취소
                </button>
                <button
                  onClick={runImport}
                  disabled={preview.imported === 0}
                  className="rounded-md bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-800 disabled:opacity-40"
                >
                  Import 실행
                </button>
              </div>
              {preview.imported === 0 && (
                <div className="mt-2 text-center text-xs text-gray-400">신규 거래가 없어 가져올 항목이 없습니다.</div>
              )}
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-6">
          <div className="mb-3 text-sm font-medium text-emerald-800">
            ✓ {SOURCE_LABEL[result.source] ?? result.source} 가져오기 완료 (batch #{result.batch_id})
          </div>
          <div className="grid grid-cols-5 gap-3 text-center text-sm">
            <Stat label="전체" value={result.total} />
            <Stat label="신규 저장" value={result.imported} tone="positive" />
            <Stat label="중복 제외" value={result.duplicates} tone="muted" />
            <Stat label="분류 완료" value={result.classified} tone="positive" />
            <Stat label="미분류" value={result.unclassified} tone="warning" />
          </div>
          <div className="mt-5 flex justify-end">
            <button onClick={reset} className="rounded-md bg-gray-900 px-4 py-2 text-sm text-white hover:bg-gray-800">
              다른 파일 가져오기
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function Stat({ label, value, tone = 'default' }: { label: string; value: number; tone?: 'default' | 'positive' | 'warning' | 'muted' }) {
  const toneClass = {
    default: 'text-gray-900',
    positive: 'text-emerald-600',
    warning: 'text-amber-600',
    muted: 'text-gray-400',
  }[tone]
  return (
    <div className="rounded-md bg-white px-2 py-3">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`text-lg font-semibold ${toneClass}`}>{value}건</div>
    </div>
  )
}
