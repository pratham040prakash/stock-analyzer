export default function DemoDecisionCard() {
  return (
    <div className="relative bg-gradient-to-r from-slate-900 to-slate-800 border border-white/10 rounded-2xl p-5 space-y-4 shadow-[0_0_40px_rgba(59,130,246,0.08)]">
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs text-gray-400 uppercase tracking-wider">
          Example · Today&apos;s decision
        </div>
        <span className="text-[10px] uppercase tracking-wider text-teal-400/70 border border-teal-500/20 rounded-full px-2 py-0.5">
          Preview
        </span>
      </div>

      <div>
        <p className="text-sm text-gray-400 mb-1">Decision</p>
        <p className="text-2xl font-semibold text-teal-300">
          Buy more
          <span className="text-base text-gray-400 font-normal ml-2">
            · 82% confidence
          </span>
        </p>
      </div>

      <div className="pt-3 border-t border-white/10">
        <p className="text-xs text-gray-400 mb-1">Reason</p>
        <p className="text-sm text-gray-300">
          You&apos;re investing below your capacity
        </p>
      </div>

      <div className="pt-3 border-t border-white/10">
        <p className="text-xs text-gray-400 mb-2">Actions</p>
        <ul className="space-y-1.5 text-sm text-gray-400">
          <li>• Add ₹10,000 this month</li>
          <li>• Diversify your portfolio</li>
        </ul>
      </div>
    </div>
  );
}
