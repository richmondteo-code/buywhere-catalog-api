import { Metadata } from "next";
import USProductDetail from "@/components/USProductDetail";
import { resolveUSProductRoute } from "@/lib/us-product-route";

interface PageProps {
  params: { productId: string };
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedProduct = await resolveUSProductRoute(params.productId);
  const productName = resolvedProduct?.name || `US Product ${params.productId}`;
  const productSlug = resolvedProduct?.slug || params.productId;
  const description = `Compare prices for ${productName} across Amazon, Walmart, Target, and Best Buy.`;
  const canonicalUrl = `https://buywhere.ai/products/us/${productSlug}`;
  const pageUrl = `https://buywhere.ai/compare/us/${params.productId}`;

  return {
    title: `${productName} - BuyWhere`,
    description,
    alternates: {
      canonical: canonicalUrl,
    },
    openGraph: {
      title: `${productName} - BuyWhere`,
      description,
      url: pageUrl,
      type: "website",
      images: [
        {
          url: "https://buywhere.ai/assets/img/og-image.png",
          width: 1200,
          height: 630,
          alt: `${productName} - Compare prices on BuyWhere US`,
        },
        {
          url: "https://buywhere.ai/assets/img/og-image.svg",
          width: 1200,
          height: 630,
          alt: `${productName} - Compare prices on BuyWhere US`,
        },
      ],
    },
  };
}

export default function USProductPage({ params }: PageProps) {
  return <USProductDetail productId={params.productId} />;
}
