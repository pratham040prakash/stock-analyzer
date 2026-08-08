import type { ReactNode } from "react";

type Props = {
  id?: string;
  children: ReactNode;
  className?: string;
  narrow?: boolean;
};

export default function LandingSection({
  id,
  children,
  className = "",
  narrow = false,
}: Props) {
  return (
    <section
      id={id}
      className={[
        "px-5 sm:px-6",
        narrow ? "max-w-[640px] mx-auto" : "max-w-5xl mx-auto",
        className,
      ].join(" ")}
    >
      {children}
    </section>
  );
}
