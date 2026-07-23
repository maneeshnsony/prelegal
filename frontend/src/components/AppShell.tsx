"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearSession, getSession } from "@/lib/session";
import DisclaimerBanner from "@/components/DisclaimerBanner";

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const router = useRouter();
  const session = getSession();

  function handleSignOut() {
    clearSession();
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen flex-col bg-zinc-50">
      <header className="border-b border-gray-200 bg-white px-6 py-3">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
          <div className="flex items-center gap-6">
            <span className="text-lg font-bold text-[#032147]">Prelegal</span>
            <Link href="/documents" className="text-sm font-medium text-[#209dd7] hover:underline">
              My Documents
            </Link>
          </div>
          <div className="flex items-center gap-4">
            {session && <span className="text-sm text-[#888888]">{session.email}</span>}
            <button
              type="button"
              onClick={handleSignOut}
              className="rounded-md border border-[#753991] px-3 py-1.5 text-sm font-medium text-[#753991] hover:bg-[#753991] hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">{children}</main>

      <DisclaimerBanner variant="footer" />
    </div>
  );
}
