export interface ProductPrice {
  amount: number | null;
  currency: string;
}

export interface ComparisonAttribute {
  key: string;
  label: string;
  value: unknown;
}

export interface CanonicalProduct {
  id: string;
  title: string;
  price: ProductPrice;
  merchant: string;
  url: string;
  image_url: string | null;
  region: string | null;
  country_code: string | null;
  updated_at: string | null;
  // Compact-mode only (agent-optimized extras):
  canonical_id?: string;
  normalized_price_usd?: number | null;
  structured_specs?: Record<string, unknown>;
  comparison_attributes?: ComparisonAttribute[];
  // Non-compact-only (legacy extras):
  metadata?: Record<string, unknown> | null;
<<<<<<< HEAD
  // Affiliate link (when available):
  affiliate_url?: string | null;
=======
>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)
  // Deal-specific:
  original_price?: number | null;
  discount_pct?: number | null;
}

export interface SearchResponse {
  results: CanonicalProduct[];
  total: number;
  page: { limit: number; offset: number };
  response_time_ms: number;
  cached: boolean;
}
