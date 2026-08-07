import { Suspense } from "react";
import LoginForm from "@/components/LoginForm";

function LoginFallback() {
  return (
    <main className="min-h-screen bg-slate-950 text-gray-200 flex items-center justify-center px-6 py-10">
      <p className="text-sm text-gray-400 italic">Setting things up for you…</p>
    </main>
  );
}

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-slate-950 text-gray-200 flex items-center justify-center px-6 py-10">
      <Suspense fallback={<LoginFallback />}>
        <LoginForm />
      </Suspense>
    </main>
  );
}
