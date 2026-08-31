import { useEffect, useState } from 'react'

interface QueryState<T> {
  data: T | undefined
  loading: boolean
  error: string | null
}

/** Minimal fetch-on-dependency-change hook - deliberately no caching
 * library here, this app's data volume and screen count don't need one. */
export function useApiQuery<T>(fetcher: () => Promise<T>, deps: unknown[]): QueryState<T> & { reload: () => void } {
  const [state, setState] = useState<QueryState<T>>({ data: undefined, loading: true, error: null })
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let cancelled = false
    setState((s) => ({ ...s, loading: true, error: null }))
    fetcher()
      .then((data) => {
        if (!cancelled) setState({ data, loading: false, error: null })
      })
      .catch((err: Error) => {
        if (!cancelled) setState({ data: undefined, loading: false, error: err.message })
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  return { ...state, reload: () => setTick((t) => t + 1) }
}
