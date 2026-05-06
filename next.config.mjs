/** @type {import('next').NextConfig} */
const nextConfig = {
  trailingSlash: true,
  output: 'standalone',
  distDir: '.next-deploy',

  async redirects() {
    return [
      // Dead developer pages → integrate
      { source: '/developers/ai-shopping-api', destination: '/integrate/', permanent: true },

      // Dead about pages → home
      { source: '/about/price-comparison', destination: '/', permanent: true },

      // Dead guides (all) → developers
      { source: '/guides/:path*', destination: '/developers', permanent: true },

      // Singular category → plural categories
      { source: '/category/:slug*', destination: '/categories/:slug*', permanent: true },

      // Legacy v1/search → canonical /search (query params auto-forwarded)
      { source: '/v1/search', destination: '/search', permanent: true },

      // Explicit 301 for merchants trailing slash (override default 308)
      { source: '/merchants', destination: '/merchants/', permanent: true },
    ];
  },
};

export default nextConfig;
