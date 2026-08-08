import { Suspense } from "react";
import LoginForm from "@/components/LoginForm";
import { ApexBody, ApexShell } from "@/components/ui/apex";

function LoginFallback() {
  return (
    <ApexShell>
      <div className="flex min-h-[50vh] items-center justify-center">
        <ApexBody className="italic">Setting things up for you…</ApexBody>
      </div>
    </ApexShell>
  );
}

export default function LoginPage() {
  return (
    <ApexShell>
      <div className="flex min-h-[70vh] items-center justify-center">
        <Suspense fallback={<LoginFallback />}>
          <LoginForm />
        </Suspense>
      </div>
    </ApexShell>
  );
}
