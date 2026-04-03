import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BuyWhere — The Product Catalog API for AI Agent Commerce",
  description:
    "Query millions of products across Southeast Asia. Structured, normalized, agent-ready.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased bg-white text-gray-900">
        {children}
      </body>
    </html>
  );
}
