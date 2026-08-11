import { AskProvider } from "@/components/ask/AskProvider";
import AskFab from "@/components/ask/AskFab";

export default function AppShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AskProvider>
      {children}
      <AskFab />
    </AskProvider>
  );
}
