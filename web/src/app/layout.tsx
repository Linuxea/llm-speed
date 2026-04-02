import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LLM Speed Monitor",
  description: "实时监控大模型 API 性能",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
