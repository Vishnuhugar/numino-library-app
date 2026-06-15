"use client";
import React from 'react';

type Props = { children: React.ReactNode };

export default class ErrorBoundary extends React.Component<Props, { hasError: boolean; error?: Error }> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: any) {
    // TODO: report to logging service
    // eslint-disable-next-line no-console
    console.error('Uncaught error:', error, info);
    this.setState({ error });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8">
          <h2 className="header-title">Something went wrong</h2>
          <div className="header-sub">An unexpected error occurred. Try refreshing the page.</div>
          {this.state.error && <pre className="error-stack">{String(this.state.error.message)}</pre>}
        </div>
      );
    }
    return this.props.children as any;
  }
}
