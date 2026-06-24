import type { Metadata } from "next";
import Link from "next/link";
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
                <span>이직각</span>
              </Link>
              <div className="flex items-center gap-1">
                <Link
                  href="/"
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9] hover:text-[#0f172a]"
                >
                  홈
                </Link>
                <Link
                  href="/compare"
                  className="rounded-md px-3 py-1.5 text-sm font-medium text-[#64748b] transition-colors hover:bg-[#f1f5f9] hover:text-[#0f172a]"
                >
                  비교하기
                </Link>
                <Link
                  href="/profile"
                  className="ml-1 rounded-md bg-[#eff6ff] px-3 py-1.5 text-sm font-medium text-[#3b82f6] transition-colors hover:bg-[#dbeafe]"
                >
                  내 정보
                </Link>
              </div>
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
