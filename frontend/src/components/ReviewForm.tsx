import { ExtractedData } from "../services/api";

type Props = {
  data: ExtractedData;
  onChange: (data: ExtractedData) => void;
};

export default function ReviewForm({ data, onChange }: Props) {
  const visualNotes = data.visual_notes ?? [];

  function patch(path: "client_details" | "job_details", field: string, value: string) {
    onChange({ ...data, [path]: { ...data[path], [field]: value } });
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
      <section className="rounded border border-stone-200 bg-white p-4">
        <h2 className="font-semibold">Client</h2>
        {["name", "phone", "email", "address"].map((field) => (
          <label key={field} className="mt-3 block text-sm">
            <span className="font-medium capitalize">{field}</span>
            <input className="focus-ring mt-1 w-full rounded border border-stone-300 px-3 py-2" value={(data.client_details as Record<string, string | null | undefined>)[field] ?? ""} onChange={(event) => patch("client_details", field, event.target.value)} />
          </label>
        ))}
      </section>
      <section className="rounded border border-stone-200 bg-white p-4">
        <h2 className="font-semibold">Job</h2>
        {["location", "job_type", "estimated_cost"].map((field) => (
          <label key={field} className="mt-3 block text-sm">
            <span className="font-medium capitalize">{field.replace("_", " ")}</span>
            <input className="focus-ring mt-1 w-full rounded border border-stone-300 px-3 py-2" value={String((data.job_details as Record<string, string | number | null | undefined>)[field] ?? "")} onChange={(event) => patch("job_details", field, event.target.value)} />
          </label>
        ))}
      </section>
      <section className="rounded border border-stone-200 bg-white p-4">
        <h2 className="font-semibold">Findings</h2>
        <textarea className="focus-ring mt-3 min-h-40 w-full rounded border border-stone-300 px-3 py-2" value={data.findings.map((item) => `${item.category}: ${item.description}`).join("\n")} onChange={(event) => onChange({ ...data, findings: event.target.value.split("\n").filter(Boolean).map((line) => ({ category: line.split(":")[0] || "Finding", description: line.split(":").slice(1).join(":").trim() || line })) })} />
      </section>
      <section className="rounded border border-stone-200 bg-white p-4">
        <h2 className="font-semibold">Follow-up</h2>
        <textarea className="focus-ring mt-3 min-h-40 w-full rounded border border-stone-300 px-3 py-2" value={data.follow_up_actions.map((item) => item.task).join("\n")} onChange={(event) => onChange({ ...data, follow_up_actions: event.target.value.split("\n").filter(Boolean).map((task) => ({ task })) })} />
      </section>
      <section className="rounded border border-stone-200 bg-white p-4 lg:col-span-2">
        <h2 className="font-semibold">Visual notes</h2>
        <textarea
          className="focus-ring mt-3 min-h-40 w-full rounded border border-stone-300 px-3 py-2"
          value={visualNotes
            .map((item) => {
              const page = item.page ? `Page ${item.page}` : "Page unknown";
              const relevance = item.relevance ? ` - ${item.relevance}` : "";
              return `${page} | ${item.visual_type}: ${item.description}${relevance}`;
            })
            .join("\n")}
          onChange={(event) =>
            onChange({
              ...data,
              visual_notes: event.target.value
                .split("\n")
                .filter(Boolean)
                .map((line) => ({ visual_type: "other", description: line })),
            })
          }
        />
      </section>
      <section className="rounded border border-stone-200 bg-white p-4 lg:col-span-2">
        <h2 className="font-semibold">Raw text</h2>
        <textarea className="focus-ring mt-3 min-h-48 w-full rounded border border-stone-300 px-3 py-2" value={data.raw_text} onChange={(event) => onChange({ ...data, raw_text: event.target.value })} />
      </section>
    </div>
  );
}
