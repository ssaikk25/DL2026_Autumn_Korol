import type {
  CurrentWeatherResponse,
  FeedbackOut,
  ForecastResponse,
  GeocodeResponse,
  LocationQuery,
  MemeListResponse,
  MemeOut,
} from '../types'

const BASE = import.meta.env.VITE_API_BASE ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const message = body && typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}`
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

function locationQuery(location: LocationQuery): string {
  const params = new URLSearchParams()
  if ('city' in location) {
    params.set('city', location.city)
  } else {
    params.set('lat', String(location.lat))
    params.set('lon', String(location.lon))
  }
  return params.toString()
}

export function searchCity(query: string): Promise<GeocodeResponse> {
  return request(`/api/geocode?q=${encodeURIComponent(query)}&limit=5`)
}

export function getCurrent(location: LocationQuery): Promise<CurrentWeatherResponse> {
  return request(`/api/weather/current?${locationQuery(location)}`)
}

export function getForecast(location: LocationQuery, days = 5): Promise<ForecastResponse> {
  return request(`/api/weather/forecast?${locationQuery(location)}&days=${days}`)
}

export function getMemes(category: string, limit = 6): Promise<MemeListResponse> {
  return request(`/api/memes?category=${category}&limit=${limit}&random=true`)
}

export function sendFeedback(
  memeId: number,
  vote: 'up' | 'down',
  category: string,
): Promise<FeedbackOut> {
  return request(`/api/memes/${memeId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vote, category }),
  })
}

export function createMeme(image: File, description: string): Promise<MemeOut> {
  const form = new FormData()
  form.append('image', image)
  form.append('description', description)
  return request('/api/memes', { method: 'POST', body: form })
}
