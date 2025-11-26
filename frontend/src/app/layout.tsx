/**
 * Root Layout for AURORA_LIFE
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Providers } from './providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AURORA LIFE - AI-Powered Life Management',
  description:
    'Transform your life with AI-powered insights, predictions, and personalized recommendations',
  keywords: ['life management', 'AI', 'productivity', 'wellness', 'insights'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
