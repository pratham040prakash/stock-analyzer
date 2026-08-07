export default function Loading() {
  return (
    <main className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-gray-400">
        <div className="h-8 w-8 rounded-full border-2 border-teal-400/30 border-t-teal-400 animate-spin" />
        <p className="text-sm">Loading your portfolio...</p>
      </div>
    </main>
  );
}
