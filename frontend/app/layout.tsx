import type { Metadata } from "next";
import Link from "next/link";
import HeaderNav from "@/components/HeaderNav";
import ThemeRegistry from "@/components/ThemeRegistry";
import "./globals.css";

export const metadata: Metadata = {
  title: "이직각",
  description: "국민연금 데이터 기반 기업 건강도 & 이직 추천도",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <ThemeRegistry>
          <header className="sticky top-0 z-50 border-b border-[#e2e8f0] bg-white shadow-sm">
            <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <Link
                href="/"
                className="flex items-center gap-2 text-lg font-bold text-[#0f172a]"
              >
                <span aria-hidden>🧭</span>
              </Link>
              <HeaderNav />
            </nav>
          </header>
          <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
            {children}
          </main>
        </ThemeRegistry>
      </body>
    </html>
  );
}
