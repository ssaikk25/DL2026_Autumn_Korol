export type WeatherCategory = 'hot' | 'cold' | 'rain' | 'snow' | 'wind' | 'comfort'

export interface GeocodeResult {
  name: string
  country?: string | null
  admin1?: string | null
  latitude: number
  longitude: number
  timezone?: string | null
}

export interface GeocodeResponse {
  results: GeocodeResult[]
}

export interface CurrentWeather {
  temperature: number
  apparent_temperature: number
  humidity: number
  wind_speed: number
  cloud_cover: number
  pressure: number
  weather_code: number
  description: string
  category: WeatherCategory
}

export interface MemeOut {
  id: number
  image_url: string
  category: string
}

export interface MemeListResponse {
  memes: MemeOut[]
}

export interface CurrentWeatherResponse {
  location: Record<string, unknown>
  current: CurrentWeather
  meme: MemeOut | null
  is_demo: boolean
}

export interface ForecastDay {
  date: string
  weather_code: number
  temp_min: number
  temp_max: number
  category: WeatherCategory
  description: string
  meme: MemeOut | null
}

export interface ForecastResponse {
  location: Record<string, unknown>
  days: ForecastDay[]
  is_demo: boolean
}

export interface FeedbackOut {
  meme_id: number
  likes: number
  dislikes: number
  alpha: number
  beta: number
}

export type LocationQuery =
  | { city: string }
  | { lat: number; lon: number }
