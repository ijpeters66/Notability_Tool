import { ChangeEvent, DragEvent, useState } from "react";
import { Upload } from "lucide-react";

type Props = {
  onUpload: (file: File) => Promise<void>;
};

export default function UploadForm({ onUpload }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(file?: File) {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  function drop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    submit(event.dataTransfer.files[0]);
  }

  function select(event: ChangeEvent<HTMLInputElement>) {
    submit(event.target.files?.[0]);
  }

  return (
    <div>
      <label onDragOver={(event) => event.preventDefault()} onDrop={drop} className="focus-ring flex min-h-56 cursor-pointer flex-col items-center justify-center rounded border-2 border-dashed border-stone-300 bg-white px-6 text-center hover:border-emerald-600">
        <Upload size={34} aria-hidden="true" />
        <span className="mt-3 font-medium">{busy ? "Uploading..." : "Drop a Notability PDF or choose one"}</span>
        <span className="mt-1 text-sm text-stone-600">PDF only, 10 MB maximum</span>
        <input type="file" accept="application/pdf" className="sr-only" onChange={select} disabled={busy} />
      </label>
      {error && <p className="mt-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
    </div>
  );
}
