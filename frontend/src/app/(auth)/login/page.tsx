// File: page.tsx. Description: User login page. Consists of: Login form, state management, error handling, and redirection logic.
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await auth.login(form);
      router.push(user.is_owner ? "/owner" : "/");
    } catch (err: any) {
      console.error("Login failed:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="glass-card w-full max-w-md space-y-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-app-accent to-purple-400 bg-clip-text text-transparent">
            AI Research Assistant
          </h1>
          <p className="text-text-secondary mt-2">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            id="login-username"
            className="input-field"
            placeholder="Username"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            id="login-password"
            type="password"
            className="input-field"
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          {error && <p className="text-danger text-sm">{error}</p>}
          <button id="login-submit" type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="text-center text-text-secondary text-sm">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-app-accent hover:text-app-accent-hover transition-colors">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
