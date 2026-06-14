import type { Metadata } from 'next';
import './globals.css';
import { UIProvider } from '@/components/ui/UIProvider';

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
        {/* Global UI provider for toasts and confirm dialogs */}
        <ProvidersWrapper>{children}</ProvidersWrapper>
      </body>
    </html>
  );
}

function ProvidersWrapper({ children }: { children: React.ReactNode }) {
  return (
    <UIProvider>
      {children}
    </UIProvider>
  );
}
