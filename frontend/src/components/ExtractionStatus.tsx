export default function ExtractionStatus({ status, error }: { status: string; error?: string | null }) {
  const busy = status === "pending" || status === "processing" || status === "pushing";
  return (
    <div className="flex items-center gap-3 rounded border border-stone-200 bg-white px-4 py-3 text-sm">
      {busy && <span className="h-3 w-3 animate-pulse rounded-full bg-emerald-600" />}
      <span className="font-medium">Status: {status}</span>
      {error && <span className="text-red-700">{error}</span>}
    </div>
  );
}
