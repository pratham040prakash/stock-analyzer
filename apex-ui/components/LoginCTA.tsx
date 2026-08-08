"use client";

import Link from "next/link";
import { ApexBody, ApexButton, ApexCard } from "@/components/ui/apex";

export default function LoginCTA() {
  return (
    <ApexCard>
      <ApexBody>
        Sign in to connect your portfolio and get one clear action for today.
      </ApexBody>
      <Link href="/login" className="mt-5 block">
        <ApexButton>Sign In to Get Started</ApexButton>
      </Link>
    </ApexCard>
  );
}
