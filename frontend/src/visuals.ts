import type { WeatherCategory } from './types'

export interface CategoryVisual {
  emoji: string
  gradient: string
  label: string
}

export const CATEGORY_VISUALS: Record<WeatherCategory, CategoryVisual> = {
  hot: {
    emoji: '☀️',
    gradient: 'from-orange-400 via-red-400 to-rose-500',
    label: 'Жарко',
  },
  cold: {
    emoji: '🥶',
    gradient: 'from-sky-400 via-blue-400 to-indigo-500',
    label: 'Холодно',
  },
  rain: {
    emoji: '🌧️',
    gradient: 'from-slate-500 via-slate-600 to-blue-800',
    label: 'Дождливо',
  },
  snow: {
    emoji: '🌨️',
    gradient: 'from-sky-200 via-blue-300 to-slate-400',
    label: 'Снежно',
  },
  wind: {
    emoji: '💨',
    gradient: 'from-teal-400 via-cyan-500 to-sky-600',
    label: 'Ветрено',
  },
  comfort: {
    emoji: '🌤️',
    gradient: 'from-emerald-400 via-teal-400 to-sky-500',
    label: 'Комфортно',
  },
}

export function visualFor(category: string): CategoryVisual {
  return CATEGORY_VISUALS[category as WeatherCategory] ?? CATEGORY_VISUALS.comfort
}

export const CATEGORY_COLORS: Record<WeatherCategory, [string, string]> = {
  hot: ['#fb923c', '#e11d48'],
  cold: ['#38bdf8', '#4338ca'],
  rain: ['#64748b', '#1e3a8a'],
  snow: ['#bae6fd', '#94a3b8'],
  wind: ['#2dd4bf', '#0284c7'],
  comfort: ['#34d399', '#0ea5e9'],
}
