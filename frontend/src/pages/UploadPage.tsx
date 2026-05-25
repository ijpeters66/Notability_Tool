import { useNavigate } from "react-router-dom";
import UploadForm from "../components/UploadForm";
import { api } from "../services/api";

export default function UploadPage() {
  const navigate = useNavigate();

  async function upload(file: File) {
    const body = new FormData();
    body.append("file", file);
    const result = await api.post<{ consultation_id: number }>("/consultations/upload", body);
    navigate(`/consultation/${result.consultation_id}`);
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-5">
        <h1 className="text-2xl font-semibold">Upload consultation notes</h1>
        <p className="mt-1 text-sm text-stone-600">Start with the PDF exported from Notability.</p>
      </div>
      <UploadForm onUpload={upload} />
    </main>
  );
}
