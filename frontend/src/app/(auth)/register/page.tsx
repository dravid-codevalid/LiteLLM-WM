// File: page.tsx. Description: User registration page. Consists of: Registration form, validation, and auto-login redirection logic.
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await auth.register(form);
      router.push("/workspaces");
    } catch (err: any) {
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
            Create Account
          </h1>
          <p className="text-text-secondary mt-2">Join the AI Research platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            id="register-username"
            className="input-field"
            placeholder="Username (3-15 chars)"
            maxLength={15}
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            id="register-email"
            type="email"
            className="input-field"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
          <input
            id="register-password"
            type="password"
            className="input-field"
            placeholder="Password (6-20 chars)"
            maxLength={20}
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
          {error && <p className="text-danger text-sm">{error}</p>}
          <button id="register-submit" type="submit" className="btn-primary w-full" disabled={loading}>
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-text-secondary text-sm">
          Already have an account?{" "}
          <Link href="/login" className="text-app-accent hover:text-app-accent-hover transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
