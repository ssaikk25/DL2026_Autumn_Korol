import type { CurrentWeather } from '../types'
import { visualFor } from '../visuals'

interface Props {
  weather: CurrentWeather
  locationName: string
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/10 px-3 py-2">
      <p className="text-xs text-white/60">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  )
}

export default function WeatherCard({ weather, locationName }: Props) {
  const visual = visualFor(weather.category)

  return (
    <div className="animate-fade-in-up rounded-2xl bg-white/15 p-6 text-white shadow-xl backdrop-blur-md">
      <div className="flex items-center gap-4">
        <span className="text-6xl">{visual.emoji}</span>
        <div>
          <p className="text-sm uppercase tracking-wide text-white/70">{locationName}</p>
          <p className="text-6xl font-bold leading-none">{Math.round(weather.temperature)}°</p>
        </div>
      </div>
      <p className="mt-3 text-lg">{weather.description}</p>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <Stat label="Ощущается" value={`${Math.round(weather.apparent_temperature)}°`} />
        <Stat label="Влажность" value={`${weather.humidity}%`} />
        <Stat label="Ветер" value={`${weather.wind_speed} м/с`} />
        <Stat label="Облачность" value={`${weather.cloud_cover}%`} />
      </div>
    </div>
  )
}
