import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ActionButtons from "../components/ActionButtons";
import ExtractionStatus from "../components/ExtractionStatus";
import PushConfirmation from "../components/PushConfirmation";
import PushError from "../components/PushError";
import PushProgress from "../components/PushProgress";
import PushSuccess from "../components/PushSuccess";
import ReviewForm from "../components/ReviewForm";
import { api, Consultation, ExtractedData } from "../services/api";

export default function ConsultationPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [consultation, setConsultation] = useState<Consultation | null>(null);
  const [data, setData] = useState<ExtractedData | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [pushError, setPushError] = useState("");

  async function load() {
    const result = await api.get<Consultation>(`/consultations/${id}`);
    setConsultation(result);
    setData(result.extracted_data ?? null);
  }

  useEffect(() => {
    load();
    const timer = window.setInterval(() => {
      if (consultation?.status === "processing" || consultation?.status === "pushing") load();
    }, 2500);
    return () => window.clearInterval(timer);
  }, [id, consultation?.status]);

  async function save() {
    if (!data) return;
    setBusy(true);
    try {
      const result = await api.put<Consultation>(`/consultations/${id}`, { extracted_data: data });
      setConsultation(result);
      setData(result.extracted_data ?? data);
    } finally {
      setBusy(false);
    }
  }

  async function reExtract() {
    const feedback = window.prompt("What should the extractor pay attention to this time?") || "";
    setBusy(true);
    try {
      await api.post(`/consultations/${id}/re-extract`, { feedback });
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    setConfirming(false);
    setBusy(true);
    setPushError("");
    try {
      await api.post(`/consultations/${id}/approve`, {});
      await load();
    } catch (err) {
      setPushError(err instanceof Error ? err.message : "Push failed");
      await load();
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!window.confirm("Delete this consultation and uploaded PDF?")) return;
    await api.delete(`/consultations/${id}`);
    navigate("/upload");
  }

  if (!consultation) return <main className="mx-auto max-w-5xl px-4 py-8">Loading...</main>;

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Review consultation #{consultation.id}</h1>
          <p className="mt-1 text-sm text-stone-600">{consultation.original_pdf_path}</p>
        </div>
        <ActionButtons onSave={save} onReExtract={reExtract} onApprove={() => setConfirming(true)} onDelete={remove} busy={busy} />
      </div>
      <div className="mb-4 space-y-3">
        <ExtractionStatus status={consultation.status} error={consultation.error_message} />
        {consultation.status === "pushing" && <PushProgress />}
        {consultation.status === "pushed" && <PushSuccess />}
        {pushError && <PushError message={pushError} onRetry={() => setConfirming(true)} />}
      </div>
      {data ? <ReviewForm data={data} onChange={setData} /> : <p className="rounded border border-stone-200 bg-white px-4 py-3">Extraction is still running.</p>}
      <PushConfirmation open={confirming} onCancel={() => setConfirming(false)} onConfirm={approve} />
    </main>
  );
}
