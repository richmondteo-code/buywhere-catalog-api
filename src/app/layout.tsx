import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BuyWhere — Product Discovery Infrastructure for AI-Powered Shopping",
  description:
    "The neutral catalog layer that AI agents use to find products and route buyers to merchants. Developers, merchants, and partners — starting with Singapore.",
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
