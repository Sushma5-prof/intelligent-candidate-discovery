import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Intelligent Candidate Discovery",
  description: "Semantic search and trajectory-aware candidate ranking.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
