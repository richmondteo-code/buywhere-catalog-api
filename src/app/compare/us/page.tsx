import dynamic from "next/dynamic";

const USPriceComparisonPage = dynamic(
  () => import("@/components/USPriceComparison"),
  {
    ssr: true,
    loading: () => (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-gray-400">Loading prices...</div>
      </div>
    ),
  }
);
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Compare US Product Prices - Amazon vs Walmart vs Target | BuyWhere",
  description: "Compare prices for popular products across Amazon, Walmart, and Target. Find the best deals on electronics, home goods, and more.",
  openGraph: {
    title: "Compare US Product Prices - Amazon vs Walmart vs Target | BuyWhere",
    description: "Compare prices for popular products across Amazon, Walmart, and Target. Find the best deals on electronics, home goods, and more.",
    type: "website",
    locale: "en_US",
    siteName: "BuyWhere US",
    images: [
      {
        url: "https://buywhere.ai/assets/img/og-image.png",
        width: 1200,
        height: 630,
        alt: "Compare US Product Prices - Amazon vs Walmart vs Target | BuyWhere",
      },
      {
        url: "https://buywhere.ai/assets/img/og-image.svg",
        width: 1200,
        height: 630,
        alt: "Compare US Product Prices - Amazon vs Walmart vs Target | BuyWhere",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Compare US Product Prices - Amazon vs Walmart vs Target | BuyWhere",
    description: "Compare prices for popular products across Amazon, Walmart, and Target. Find the best deals on electronics, home goods, and more.",
  },
  alternates: {
    canonical: "https://buywhere.ai/compare/us",
  },
};

export default function CompareUSPage() {
  return <USPriceComparisonPage />;
}