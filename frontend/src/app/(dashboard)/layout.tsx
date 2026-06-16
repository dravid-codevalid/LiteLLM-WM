// File: layout.tsx. Description: Dashboard shell layout. Consists of: Sidebar navigation, user profile display, and authentication route guard.
"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { auth, User } from "@/lib/api";

const navItems = [
  { href: "/workspaces", label: "Workspaces", icon: "◆" },
  { href: "/usage", label: "Usage", icon: "◈" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    auth.me()
      .then((u) => {
        setUser(u);
      })
      .catch((err) => {
        console.error("Auth failed in layout:", err);
        router.push("/login");
      });
  }, [router]);

  const handleLogout = async () => {
    await auth.logout();
    router.push("/login");
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-text-secondary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-bg-secondary border-r border-border flex flex-col">
        <div className="p-6 border-b border-border">
          <h2 className="font-bold text-lg bg-gradient-to-r from-app-accent to-purple-400 bg-clip-text text-transparent">
            AI Research
          </h2>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                pathname.startsWith(item.href)
                  ? "bg-app-accent/10 text-app-accent"
                  : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
              }`}
            >
              <span>{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-border space-y-3">
          <div className="px-3">
            <p className="text-sm font-medium truncate">{user.username}</p>
            <p className="text-xs text-text-secondary truncate">{user.email}</p>
          </div>
          <button onClick={handleLogout} className="btn-ghost w-full text-left text-sm">
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
