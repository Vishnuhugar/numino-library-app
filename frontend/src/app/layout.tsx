import type { Metadata } from 'next';
import './globals.css';
import { UIProvider } from '@/components/ui/UIProvider';
import ErrorBoundary from '@/components/ui/ErrorBoundary';

export const metadata: Metadata = {
  title: 'Neighborhood Library',
  description: 'Library Management System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <UIProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </UIProvider>
      </body>
    </html>
  );
}
