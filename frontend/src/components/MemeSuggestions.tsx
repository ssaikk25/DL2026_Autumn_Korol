import type { MemeOut } from '../types'

interface Props {
  memes: MemeOut[]
  selectedId: number | null
  onSelect: (meme: MemeOut) => void
}

export default function MemeSuggestions({ memes, selectedId, onSelect }: Props) {
  return (
    <div className="animate-fade-in-up">
      <p className="mb-2 text-center text-sm text-white/80">Выбери мем:</p>
      <div className="flex flex-wrap justify-center gap-2">
        {memes.map((meme) => (
          <button
            key={meme.id}
            onClick={() => onSelect(meme)}
            title="Выбрать этот мем"
            className={`overflow-hidden rounded-lg border-2 transition ${
              meme.id === selectedId
                ? 'border-white opacity-100 ring-2 ring-white/60'
                : 'border-transparent opacity-75 hover:opacity-100'
            }`}
          >
            <img src={meme.image_url} alt="Мем" className="h-20 w-20 object-cover" />
          </button>
        ))}
      </div>
    </div>
  )
}
