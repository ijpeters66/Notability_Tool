export default function PushError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      <p>{message}</p>
      <button className="focus-ring mt-3 rounded border border-red-300 bg-white px-3 py-2" onClick={onRetry}>Retry</button>
    </div>
  );
}
