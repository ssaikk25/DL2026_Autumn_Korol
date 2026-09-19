import type { ForecastDay } from '../types'
import { visualFor } from '../visuals'
import MemeCard from './MemeCard'

interface Props {
  day: ForecastDay
  onRate: (vote: 'up' | 'down') => void
  onBack: () => void
}

function formatDate(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
}

export default function ForecastDayDetail({ day, onRate, onBack }: Props) {
  const visual = visualFor(day.category)
  return (
    <div className="space-y-4">
      <button
        onClick={onBack}
        className="rounded-xl bg-white/20 px-4 py-2 text-sm font-medium text-white backdrop-blur transition hover:bg-white/30"
      >
        ← Назад к сегодня
      </button>

      <div className="animate-fade-in-up rounded-2xl bg-white/15 p-6 text-center text-white shadow-xl backdrop-blur-md">
        <p className="text-sm uppercase tracking-wide text-white/70">{formatDate(day.date)}</p>
        <p className="text-6xl">{visual.emoji}</p>
        <p className="text-3xl font-bold">
          {Math.round(day.temp_max)}° / {Math.round(day.temp_min)}°
        </p>
        <p className="mt-2 text-lg">{day.description}</p>
      </div>

      {day.meme && <MemeCard meme={day.meme} onRate={onRate} />}
    </div>
  )
}
