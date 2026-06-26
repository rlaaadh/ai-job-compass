import type { CompanyBasic, HealthScore, CompareResult, CompareRequest } from './types'

function resolveBaseUrl(): string {
  const envValue = process.env.NEXT_PUBLIC_API_URL?.trim()
  if (envValue && /^https?:\/\//.test(envValue)) {
    return envValue.replace(/\/$/, '')
  }

  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8100'
    }
  }

  return (envValue || 'http://localhost:8100').replace(/\/$/, '')
}

const BASE_URL = resolveBaseUrl()

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

type SearchCompaniesOptions = {
  fallback?: boolean
  signal?: AbortSignal
}

export const api = {
  searchCompanies: (name: string, rows = 10, options: SearchCompaniesOptions = {}) => {
    const params = new URLSearchParams({
      name,
      rows: String(rows),
      fallback: String(options.fallback ?? true),
    })

    return fetchJSON<CompanyBasic[]>(`/companies/search?${params.toString()}`, {
      signal: options.signal,
    })
  },

  getHealth: (seq: number) =>
    fetchJSON<HealthScore>(`/companies/${seq}/health`),

  compare: (body: CompareRequest) =>
    fetchJSON<CompareResult>('/compare', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
