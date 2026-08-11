import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/components/AuthProvider";
import DevDebugBadge from "@/components/DevDebugBadge";
import { logSupabaseEnvCheck } from "@/lib/supabase/startupCheck";
import "./globals.css";

logSupabaseEnvCheck();

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "APEX — Investment Decision Platform",
  description: "Calm, evidence-aware guidance for better investing decisions.",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover" as const,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          {children}
          <DevDebugBadge />
        </AuthProvider>
      </body>
    </html>
  );
}
