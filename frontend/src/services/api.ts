export type ExtractedData = {
  client_details: { name?: string | null; phone?: string | null; email?: string | null; address?: string | null };
  job_details: { location?: string | null; job_type?: string | null; estimated_cost?: string | number | null };
  findings: Array<{ category: string; description: string }>;
  recommendations: Array<{ action: string; priority: "high" | "medium" | "low"; estimated_effort?: string | null }>;
  follow_up_actions: Array<{ task: string; due_date?: string | null; assigned_to?: string | null }>;
  visual_notes: Array<{
    page?: number | null;
    visual_type: "drawing" | "photo" | "diagram" | "other";
    description: string;
    relevance?: string | null;
  }>;
  raw_text: string;
};

export type Consultation = {
  id: number;
  status: string;
  error_message?: string | null;
  original_pdf_path: string;
  extracted_data?: ExtractedData | null;
  created_at: string;
  updated_at: string;
};

export class ApiClient {
  baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  token = localStorage.getItem("notability_token");

  setToken(token: string | null) {
    this.token = token;
    if (token) localStorage.setItem("notability_token", token);
    else localStorage.removeItem("notability_token");
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
    if (this.token) headers.set("Authorization", `Bearer ${this.token}`);

    const response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Request failed");
    }
    return response.json();
  }

  get<T>(path: string) {
    return this.request<T>(path);
  }

  post<T>(path: string, body?: unknown) {
    return this.request<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });
  }

  put<T>(path: string, body: unknown) {
    return this.request<T>(path, { method: "PUT", body: JSON.stringify(body) });
  }

  delete<T>(path: string) {
    return this.request<T>(path, { method: "DELETE" });
  }
}

export const api = new ApiClient();
