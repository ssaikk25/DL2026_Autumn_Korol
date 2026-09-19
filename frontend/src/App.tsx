import { useCallback, useEffect, useState } from 'react'
import { getCurrent, getForecast, getMemes, sendFeedback } from './api/client'
import type {
  CurrentWeatherResponse,
  ForecastDay,
  ForecastResponse,
  GeocodeResult,
  LocationQuery,
  MemeOut,
} from './types'
import { CATEGORY_COLORS, visualFor } from './visuals'
import ForecastDayDetail from './components/ForecastDayDetail'
import ForecastStrip from './components/ForecastStrip'
import MemeCard from './components/MemeCard'
import MemeSuggestions from './components/MemeSuggestions'
import SearchBar from './components/SearchBar'
import WeatherCard from './components/WeatherCard'

function locationName(
  location: LocationQuery | null,
  weather: CurrentWeatherResponse | null,
): string {
  if (weather?.location?.name) {
    const name = String(weather.location.name)
    const country = weather.location.country ? String(weather.location.country) : ''
    return country ? `${name}, ${country}` : name
  }
  if (location && 'city' in location) return location.city
  return 'Ваша локация'
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = reject
    image.src = src
  })
}

export default function App() {
  const [location, setLocation] = useState<LocationQuery | null>(null)
  const [weather, setWeather] = useState<CurrentWeatherResponse | null>(null)
  const [forecast, setForecast] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toast, setToast] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<MemeOut[]>([])
  const [selectedMeme, setSelectedMeme] = useState<MemeOut | null>(null)
  const [selectedDay, setSelectedDay] = useState<ForecastDay | null>(null)

  const displayedMeme = selectedMeme ?? weather?.meme ?? null

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(null), 2500)
    return () => window.clearTimeout(timer)
  }, [toast])

  const load = useCallback(async (query: LocationQuery) => {
    setLocation(query)
    setLoading(true)
    setError(null)
    try {
      const [current, fc] = await Promise.all([getCurrent(query), getForecast(query, 5)])
      setWeather(current)
      setForecast(fc)
      setSelectedMeme(null)
      setSelectedDay(null)
      getMemes(current.current.category, 6)
        .then((data) => setSuggestions(data.memes))
        .catch(() => setSuggestions([]))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Что-то пошло не так')
    } finally {
      setLoading(false)
    }
  }, [])

  function onSelectCity(result: GeocodeResult) {
    void load({ city: result.name })
  }

  function onUseLocation() {
    if (!navigator.geolocation) {
      setError('Геолокация недоступна в этом браузере')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => void load({ lat: position.coords.latitude, lon: position.coords.longitude }),
      () => setError('Не удалось определить местоположение'),
    )
  }

  async function onRate(vote: 'up' | 'down') {
    if (!displayedMeme) return
    try {
      await sendFeedback(displayedMeme.id, vote, displayedMeme.category)
      setToast(vote === 'up' ? 'Спасибо за оценку' : 'Учтём')
    } catch {
      /* ignore rating errors */
    }
  }

  async function onRateDay(vote: 'up' | 'down') {
    if (!selectedDay?.meme) return
    try {
      await sendFeedback(selectedDay.meme.id, vote, selectedDay.category)
      setToast(vote === 'up' ? 'Спасибо за оценку' : 'Учтём')
    } catch {
      /* ignore rating errors */
    }
  }

  async function onAnother() {
    if (!location) return
    try {
      const current = await getCurrent(location)
      setWeather(current)
      setSelectedMeme(null)
      getMemes(current.current.category, 6)
        .then((data) => setSuggestions(data.memes))
        .catch(() => setSuggestions([]))
    } catch {
      /* ignore */
    }
  }

  async function buildPostcardBlob(): Promise<Blob | null> {
    if (!weather) return null
    const canvas = document.createElement('canvas')
    canvas.width = 900
    canvas.height = 1200
    const context = canvas.getContext('2d')
    if (!context) return null

    const [start, end] = CATEGORY_COLORS[weather.current.category]
    const gradient = context.createLinearGradient(0, 0, 0, canvas.height)
    gradient.addColorStop(0, start)
    gradient.addColorStop(1, end)
    context.fillStyle = gradient
    context.fillRect(0, 0, canvas.width, canvas.height)

    context.fillStyle = '#ffffff'
    context.textAlign = 'center'
    context.font = 'bold 56px system-ui'
    context.fillText(locationName(location, weather), canvas.width / 2, 110)

    context.font = 'bold 170px system-ui'
    context.fillText(`${Math.round(weather.current.temperature)}°`, canvas.width / 2, 300)

    context.font = '46px system-ui'
    context.fillText(
      `${visualFor(weather.current.category).emoji} ${weather.current.description}`,
      canvas.width / 2,
      370,
    )

    if (displayedMeme) {
      try {
        const image = await loadImage(displayedMeme.image_url)
        const maxWidth = 720
        const maxHeight = 640
        const scale = Math.min(maxWidth / image.width, maxHeight / image.height)
        const width = image.width * scale
        const height = image.height * scale
        context.drawImage(image, (canvas.width - width) / 2, 440, width, height)
      } catch {
        /* meme image optional on the postcard */
      }
    }

    return new Promise((resolve) => canvas.toBlob((blob) => resolve(blob), 'image/png'))
  }

  async function onDownload() {
    const blob = await buildPostcardBlob()
    if (!blob) return
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'weather-mood.png'
    anchor.click()
    URL.revokeObjectURL(url)
  }

  async function onShare() {
    if (!weather) return
    const text = `${locationName(location, weather)}: ${Math.round(
      weather.current.temperature,
    )}°, ${weather.current.description}`
    const blob = await buildPostcardBlob()

    // 1) Web Share API with the image file (mobile browsers).
    if (blob) {
      const file = new File([blob], 'weather-mood.png', { type: 'image/png' })
      const canShareFiles =
        typeof navigator.share === 'function' &&
        typeof navigator.canShare === 'function' &&
        navigator.canShare({ files: [file] })

      if (canShareFiles) {
        try {
          await navigator.share({ title: 'Погода с настроением', text, files: [file] })
          return
        } catch {
          return // user cancelled
        }
      }

      // 2) Copy the postcard image to the clipboard (desktop browsers).
      if (typeof ClipboardItem !== 'undefined' && navigator.clipboard) {
        try {
          await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
          setToast('Открытка скопирована в буфер обмена')
          return
        } catch {
          /* fall through to text */
        }
      }
    }

    // 3) Fallback: copy the text summary.
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text)
      setToast('Скопировано в буфер обмена')
    }
  }

  const background = weather
    ? `bg-gradient-to-br ${visualFor(weather.current.category).gradient}`
    : 'bg-gradient-to-br from-slate-700 to-slate-900'

  return (
    <div className={`min-h-screen transition-colors duration-700 ${background}`}>
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-4 py-8">
        <header className="text-center text-white">
          <h1 className="text-3xl font-bold">Погода с настроением</h1>
          <p className="mt-1 text-white/70">Введи город — получи прогноз и мем под погоду</p>
        </header>

        <div className="flex justify-center">
          <SearchBar onSelect={onSelectCity} onUseLocation={onUseLocation} />
        </div>

        {loading && (
          <div className="text-center text-white/80">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-white/30 border-t-white" />
            <p className="mt-3">Загружаем…</p>
          </div>
        )}

        {error && (
          <div className="mx-auto rounded-xl bg-red-500/90 px-5 py-3 text-center text-white shadow">
            {error}
          </div>
        )}

        {weather && !loading && (
          <>
            {selectedDay ? (
              <ForecastDayDetail
                day={selectedDay}
                onRate={(v) => void onRateDay(v)}
                onBack={() => setSelectedDay(null)}
              />
            ) : (
              <>
                {weather.is_demo && (
                  <div className="mx-auto rounded-lg bg-amber-400/90 px-4 py-1.5 text-sm font-medium text-amber-950">
                    Демо-данные (погодный сервис недоступен)
                  </div>
                )}

                <WeatherCard weather={weather.current} locationName={locationName(location, weather)} />

                {displayedMeme && (
                  <MemeCard
                    key={displayedMeme.id}
                    meme={displayedMeme}
                    onRate={(v) => void onRate(v)}
                    onAnother={() => void onAnother()}
                  />
                )}

                {suggestions.length > 1 && (
                  <MemeSuggestions
                    memes={suggestions}
                    selectedId={displayedMeme?.id ?? null}
                    onSelect={setSelectedMeme}
                  />
                )}

                <div className="flex justify-center gap-3">
                  <button
                    onClick={() => void onDownload()}
                    className="rounded-xl bg-white px-5 py-2.5 font-semibold text-slate-800 shadow transition hover:bg-slate-100"
                  >
                    ⬇ Скачать открытку
                  </button>
                  <button
                    onClick={() => void onShare()}
                    className="rounded-xl bg-white/20 px-5 py-2.5 font-semibold text-white shadow backdrop-blur transition hover:bg-white/30"
                  >
                    Поделиться
                  </button>
                </div>

                {forecast && forecast.days.length > 0 && (
                  <ForecastStrip days={forecast.days} onSelect={setSelectedDay} />
                )}
              </>
            )}
          </>
        )}

        {!weather && !loading && !error && (
          <p className="text-center text-white/60">Начни с поиска города или кнопки геолокации</p>
        )}
      </div>

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-full bg-slate-900 px-5 py-2.5 text-sm text-white shadow-lg">
          {toast}
        </div>
      )}
    </div>
  )
}
