import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Agent T - 교통 시뮬레이션 플랫폼",
  description: "AI 기반 교통 시뮬레이션 자동화 플랫폼",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
              <div className="container mx-auto flex h-16 items-center px-4">
                <Link href="/" className="flex items-center space-x-2">
                  <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                    AI Agent T
                  </span>
                </Link>
                
                <nav className="ml-auto flex gap-4 sm:gap-6">
                  <Link
                    href="/"
                    className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
                  >
                    대시보드
                  </Link>
                  <Link
                    href="/experiments/new"
                    className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
                  >
                    새 실험
                  </Link>
                </nav>
              </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
              {children}
            </main>

            {/* Footer */}
            <footer className="border-t mt-16">
              <div className="container mx-auto px-4 py-6 text-center text-sm text-muted-foreground">
                <p>AI Agent T v0.4.0 - 교통 시뮬레이션 자동화 플랫폼</p>
              </div>
            </footer>
          </div>
        </Providers>
      </body>
    </html>
  );
}
