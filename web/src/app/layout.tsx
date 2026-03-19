import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agent动物园 - Zoo Multi-Agent",
  description: "与可爱的动物伙伴们一起聊天、协作",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
