import type { ForecastDay } from '../types'
import { visualFor } from '../visuals'

interface Props {
  days: ForecastDay[]
  onSelect: (day: ForecastDay) => void
}

function formatDate(iso: string): string {
  const date = new Date(iso)
  return date.toLocaleDateString('ru-RU', { weekday: 'short', day: 'numeric' })
}

export default function ForecastStrip({ days, onSelect }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {days.map((day) => {
        const visual = visualFor(day.category)
        return (
          <button
            key={day.date}
            onClick={() => onSelect(day)}
            className="animate-fade-in-up rounded-xl bg-white/15 p-3 text-center text-white backdrop-blur-md transition hover:bg-white/30"
          >
            <p className="text-xs capitalize text-white/70">{formatDate(day.date)}</p>
            <p className="text-2xl">{visual.emoji}</p>
            <p className="text-sm font-semibold">
              {Math.round(day.temp_max)}° / {Math.round(day.temp_min)}°
            </p>
            {day.meme && (
              <img
                src={day.meme.image_url}
                alt="Мем дня"
                className="mx-auto mt-2 h-16 w-16 rounded-lg object-cover"
              />
            )}
          </button>
        )
      })}
    </div>
  )
}
