import { useEffect, useRef, useState } from 'react'
import { searchCity } from '../api/client'
import type { GeocodeResult } from '../types'

interface Props {
  onSelect: (result: GeocodeResult) => void
  onUseLocation: () => void
}

export default function SearchBar({ onSelect, onUseLocation }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<GeocodeResult[]>([])
  const [open, setOpen] = useState(false)
  const debounceRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    window.clearTimeout(debounceRef.current)
    if (query.trim().length < 2) {
      setResults([])
      setOpen(false)
      return
    }
    debounceRef.current = window.setTimeout(async () => {
      try {
        const data = await searchCity(query.trim())
        setResults(data.results)
        setOpen(true)
      } catch {
        setResults([])
      }
    }, 300)
    return () => window.clearTimeout(debounceRef.current)
  }, [query])

  function pick(result: GeocodeResult) {
    setQuery(`${result.name}${result.country ? `, ${result.country}` : ''}`)
    setOpen(false)
    onSelect(result)
  }

  return (
    <div className="relative w-full max-w-md">
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Введите город…"
          className="w-full rounded-xl border border-white/40 bg-white/90 px-4 py-3 text-slate-800 shadow outline-none backdrop-blur focus:ring-2 focus:ring-white/70"
        />
        <button
          onClick={onUseLocation}
          title="Моя локация"
          className="shrink-0 rounded-xl bg-white/90 px-4 py-3 text-lg shadow backdrop-blur hover:bg-white"
        >
          📍
        </button>
      </div>

      {open && results.length > 0 && (
        <ul className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl bg-white shadow-lg">
          {results.map((result) => (
            <li key={`${result.latitude}-${result.longitude}`}>
              <button
                onClick={() => pick(result)}
                className="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-100"
              >
                {result.name}
                {result.admin1 ? `, ${result.admin1}` : ''}
                {result.country ? `, ${result.country}` : ''}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
