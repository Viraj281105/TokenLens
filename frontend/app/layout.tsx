import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TokenLens — Intelligent LLM Cost Optimizer",
  description:
    "Cut LLM API costs by up to 60% with intelligent prompt compression, semantic caching, and complexity-based model routing. Powered by Google Gemini.",
  keywords: [
    "LLM",
    "token optimization",
    "cost reduction",
    "Gemini",
    "prompt compression",
    "AI",
  ],
  openGraph: {
    title: "TokenLens — Intelligent LLM Cost Optimizer",
    description: "Cut LLM API costs by up to 60%",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased min-h-screen bg-background text-foreground">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-lg"
        >
          Skip to main content
        </a>
        {children}
      </body>
    </html>
  );
}
