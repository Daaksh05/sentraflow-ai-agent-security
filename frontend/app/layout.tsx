import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentreFlow — AI Agent Security & Control Platform",
  description: "Real-time security and control layer for autonomous AI agents powered by deterministic policies and NVIDIA Nemotron reasoning.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen flex flex-col selection:bg-sentra-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
