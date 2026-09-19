import { useState, type FormEvent } from 'react'

interface Props {
  onSubmit: (image: File, description: string) => Promise<void>
  onCancel: () => void
}

export default function AddMemeForm({ onSubmit, onCancel }: Props) {
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!file) {
      setError('Выбери картинку')
      return
    }
    setBusy(true)
    setError(null)
    try {
      await onSubmit(file, description)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось добавить мем')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="animate-fade-in-up rounded-2xl bg-white/15 p-5 text-white shadow-xl backdrop-blur-md"
    >
      <h2 className="mb-3 text-lg font-semibold">Добавить мем</h2>

      <input
        type="file"
        accept="image/*"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        className="block w-full text-sm text-white/80 file:mr-3 file:rounded-lg file:border-0 file:bg-white file:px-3 file:py-1.5 file:font-medium file:text-slate-800"
      />

      <textarea
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Описание (поможет подобрать категорию), например «дождь и зонт»"
        rows={3}
        className="mt-3 w-full rounded-xl border border-white/30 bg-white/10 px-3 py-2 text-white placeholder-white/40 outline-none"
      />

      {error && <p className="mt-2 text-sm text-amber-200">{error}</p>}

      <div className="mt-4 flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-xl bg-white/20 px-4 py-2 text-sm font-medium transition hover:bg-white/30"
        >
          Отмена
        </button>
        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-800 transition disabled:opacity-50"
        >
          {busy ? 'Добавляем…' : 'Добавить'}
        </button>
      </div>
    </form>
  )
}
