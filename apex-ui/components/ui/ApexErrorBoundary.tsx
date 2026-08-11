"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
  fallbackTitle?: string;
};

type State = {
  hasError: boolean;
};

export default class ApexErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("APEX surface error", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <section className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-4 space-y-2">
          <p className="text-sm font-medium text-apex-text/95">
            {this.props.fallbackTitle ?? "Something went wrong on this screen."}
          </p>
          <p className="text-sm text-apex-muted/85">
            Refresh the page. If it persists, reconnect Zerodha from Settings.
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false })}
            className="rounded-lg border border-apex-border/25 px-3 py-2 text-sm text-apex-muted"
          >
            Try again
          </button>
        </section>
      );
    }

    return this.props.children;
  }
}
