export default function PushConfirmation({ open, onCancel, onConfirm }: { open: boolean; onCancel: () => void; onConfirm: () => void }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-md rounded bg-white p-5 shadow-lg">
        <h2 className="text-lg font-semibold">Approve and push?</h2>
        <p className="mt-2 text-sm text-stone-700">This will create or update records in ServiceM8 using the reviewed data.</p>
        <div className="mt-5 flex justify-end gap-2">
          <button className="focus-ring rounded border border-stone-300 px-4 py-2" onClick={onCancel}>Cancel</button>
          <button className="focus-ring rounded bg-emerald-700 px-4 py-2 font-medium text-white" onClick={onConfirm}>Push</button>
        </div>
      </div>
    </div>
  );
}
