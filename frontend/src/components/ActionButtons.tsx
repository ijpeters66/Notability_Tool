import { Check, RefreshCw, Trash2 } from "lucide-react";

type Props = {
  onSave: () => Promise<void>;
  onReExtract: () => Promise<void>;
  onApprove: () => void | Promise<void>;
  onDelete: () => Promise<void>;
  busy: boolean;
};

export default function ActionButtons({ onSave, onReExtract, onApprove, onDelete, busy }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <button className="focus-ring rounded border border-stone-300 bg-white px-4 py-2" onClick={onSave} disabled={busy}>Save edits</button>
      <button className="focus-ring flex items-center gap-2 rounded border border-stone-300 bg-white px-4 py-2" onClick={onReExtract} disabled={busy}><RefreshCw size={16} />Re-extract</button>
      <button className="focus-ring flex items-center gap-2 rounded bg-emerald-700 px-4 py-2 font-medium text-white" onClick={onApprove} disabled={busy}><Check size={16} />Approve & Push</button>
      <button className="focus-ring flex items-center gap-2 rounded border border-red-200 bg-white px-4 py-2 text-red-700" onClick={onDelete} disabled={busy}><Trash2 size={16} />Delete</button>
    </div>
  );
}
