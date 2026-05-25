import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await auth.login(email, password);
      navigate("/upload");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md items-center px-4">
      <form onSubmit={submit} className="w-full rounded border border-stone-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold">Sign in</h1>
        {error && <p className="mt-4 rounded bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <label className="mt-5 block text-sm font-medium">Email</label>
        <input className="focus-ring mt-1 w-full rounded border border-stone-300 px-3 py-2" value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
        <label className="mt-4 block text-sm font-medium">Password</label>
        <input className="focus-ring mt-1 w-full rounded border border-stone-300 px-3 py-2" value={password} onChange={(event) => setPassword(event.target.value)} type="password" required />
        <button className="focus-ring mt-6 w-full rounded bg-emerald-700 px-4 py-2 font-medium text-white">Sign in</button>
        <p className="mt-4 text-sm">No account yet? <Link className="font-medium text-emerald-700" to="/register">Create one</Link></p>
      </form>
    </main>
  );
}
