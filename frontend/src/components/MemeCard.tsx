import type { MemeOut } from '../types'

interface Props {
  meme: MemeOut
  onRate: (vote: 'up' | 'down') => void
  onAnother?: () => void
}

export default function MemeCard({ meme, onRate, onAnother }: Props) {
  return (
    <div className="animate-meme-in rounded-2xl bg-white p-3 shadow-xl">
      <img
        src={meme.image_url}
        alt="Мем про погоду"
        className="mx-auto max-h-[380px] rounded-lg object-contain"
      />
      <div className="mt-3 flex items-center justify-center gap-3">
        <button
          onClick={() => onRate('up')}
          className="rounded-full bg-slate-100 px-4 py-2 text-xl transition hover:bg-green-100"
          aria-label="Нравится"
        >
          👍
        </button>
        <button
          onClick={() => onRate('down')}
          className="rounded-full bg-slate-100 px-4 py-2 text-xl transition hover:bg-red-100"
          aria-label="Не нравится"
        >
          👎
        </button>
        {onAnother && (
          <button
            onClick={onAnother}
            className="rounded-full bg-slate-800 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
          >
            Другой мем
          </button>
        )}
      </div>
    </div>
  )
}
