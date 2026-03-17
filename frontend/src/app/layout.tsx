import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/sidebar";
import { MobileNav } from "@/components/layout/mobile-nav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Amstram — Opportunity Finder",
  description: "Outil de prospection Monga",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className={inter.className}>
        <div className="flex h-screen">
          <div className="hidden md:flex">
            <Sidebar />
          </div>
          <div className="flex flex-1 flex-col overflow-auto">
            <MobileNav />
            <main className="flex-1 overflow-auto bg-background p-4 md:p-8">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
