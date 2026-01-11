import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeSetter } from "@/components/theme-setter";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Concept Visualizer",
  description:
    "Ask how something works and get a Gemini-generated Mermaid diagram.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} antialiased`}>
        <ThemeSetter />
        {children}
      </body>
    </html>
  );
}
