type Props = {
  title?: string;
  description?: string;
  buttonLabel?: string;
  subtext?: string;
};

export default function ConnectZerodhaCard({
  title = "Let's bring your portfolio into APEX",
  description = "I'll securely connect to your broker and understand your portfolio — nothing manual needed.",
  buttonLabel = "Connect Zerodha",
  subtext = "Takes less than 10 seconds · No passwords stored",
}: Props) {
  return (
    <div className="p-6 rounded-2xl border border-white/10 bg-gradient-to-b from-slate-900 to-slate-900/80 shadow-[0_0_40px_rgba(59,130,246,0.06)]">
      <h2 className="text-xl font-semibold text-white mb-2">{title}</h2>
      <p className="text-sm text-gray-400 mb-5 max-w-md">{description}</p>

      <a href="/api/zerodha/login">
        <button
          type="button"
          className="px-5 py-2.5 rounded-lg bg-blue-600/90 hover:bg-blue-600 border border-blue-500/30 text-white text-sm font-medium transition-all active:scale-95"
        >
          {buttonLabel}
        </button>
      </a>

      <p className="text-xs text-gray-500 mt-3">{subtext}</p>

      <ul className="mt-5 space-y-2 text-sm text-gray-400">
        <li className="flex items-center gap-2">
          <span className="text-green-400">✔</span>
          Secure connection
        </li>
        <li className="flex items-center gap-2">
          <span className="text-green-400">✔</span>
          Read-only access
        </li>
        <li className="flex items-center gap-2">
          <span className="text-green-400">✔</span>
          You stay in control
        </li>
      </ul>
    </div>
  );
}
