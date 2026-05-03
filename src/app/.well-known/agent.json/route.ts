const AGENT_CARD = {
  "name": "Buywhere Product Catalog",
  "description": "Cross-border product discovery with intelligent market matching, price comparison, and affiliate attribution across Singapore, China, and global markets.",
  "url": "https://buywhere.ai",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false,
    "stateTransitionHistory": true
  },
  "authentication": {
    "schemes": [
      "apiKey",
      "oauth2"
    ]
  },
  "defaultInputModes": [
    "text"
  ],
  "defaultOutputModes": [
    "text",
    "json"
  ],
  "skills": [
    {
      "id": "product-search",
      "name": "Product Search",
      "description": "Search products by keyword, category, price range, and market",
      "tags": [
        "e-commerce",
        "search",
        "products"
      ],
      "examples": [
        "Find Dyson hair dryer under 400 SGD in Singapore",
        "Organic shampoo in China under 100 CNY"
      ]
    },
    {
      "id": "cross-border-match",
      "name": "Cross-Border Product Matching",
      "description": "Find equivalent products across different markets with price and spec comparison",
      "tags": [
        "cross-border",
        "matching",
        "price-comparison",
        "affiliate"
      ],
      "examples": [
        "What is the China equivalent of this Singapore shampoo?",
        "Find the cheapest market for iPhone 16 Pro Max"
      ]
    },
    {
      "id": "price-history",
      "name": "Price History & Alerts",
      "description": "Retrieve historical price data and set up price drop alerts",
      "tags": [
        "pricing",
        "history",
        "alerts"
      ],
      "examples": [
        "Show me 30-day price history for this product",
        "Alert me when this drops below 50 SGD"
      ]
    },
    {
      "id": "merchant-discovery",
      "name": "Merchant & Affiliate Discovery",
      "description": "Discover merchants selling a product and retrieve affiliate links",
      "tags": [
        "merchants",
        "affiliate",
        "deals"
      ],
      "examples": [
        "Which merchants sell this product in China?",
        "Get affiliate link for this Singapore merchant"
      ]
    }
  ],
  "signature": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXUyIsImtpZCI6ImJ1eXdoZXJlLWFnZW50LWNhcmQifQ.eyJuYW1lIjoiQnV5d2hlcmUgUHJvZHVjdCBDYXRhbG9nIiwiZGVzY3JpcHRpb24iOiJDcm9zcy1ib3JkZXIgcHJvZHVjdCBkaXNjb3Zlcnkgd2l0aCBpbnRlbGxpZ2VudCBtYXJrZXQgbWF0Y2hpbmcsIHByaWNlIGNvbXBhcmlzb24sIGFuZCBhZmZpbGlhdGUgYXR0cmlidXRpb24gYWNyb3NzIFNpbmdhcG9yZSwgQ2hpbmEsIGFuZCBnbG9iYWwgbWFya2V0cy4iLCJ1cmwiOiJodHRwczovL2J1eXdoZXJlLmFpIiwidmVyc2lvbiI6IjEuMC4wIiwiY2FwYWJpbGl0aWVzIjp7InN0cmVhbWluZyI6dHJ1ZSwicHVzaE5vdGlmaWNhdGlvbnMiOmZhbHNlLCJzdGF0ZVRyYW5zaXRpb25IaXN0b3J5Ijp0cnVlfSwiYXV0aGVudGljYXRpb24iOnsic2NoZW1lcyI6WyJhcGlLZXkiLCJvYXV0aDIiXX0sImRlZmF1bHRJbnB1dE1vZGVzIjpbInRleHQiXSwiZGVmYXVsdE91dHB1dE1vZGVzIjpbInRleHQiLCJqc29uIl0sInNraWxscyI6W3siaWQiOiJwcm9kdWN0LXNlYXJjaCIsIm5hbWUiOiJQcm9kdWN0IFNlYXJjaCIsImRlc2NyaXB0aW9uIjoiU2VhcmNoIHByb2R1Y3RzIGJ5IGtleXdvcmQsIGNhdGVnb3J5LCBwcmljZSByYW5nZSwgYW5kIG1hcmtldCIsInRhZ3MiOlsiZS1jb21tZXJjZSIsInNlYXJjaCIsInByb2R1Y3RzIl0sImV4YW1wbGVzIjpbIkZpbmQgRHlzb24gaGFpciBkcnllciB1bmRlciA0MDAgU0dEIGluIFNpbmdhcG9yZSIsIk9yZ2FuaWMgc2hhbXBvbyBpbiBDaGluYSB1bmRlciAxMDAgQ05ZIl19LHsiaWQiOiJjcm9zcy1ib3JkZXItbWF0Y2giLCJuYW1lIjoiQ3Jvc3MtQm9yZGVyIFByb2R1Y3QgTWF0Y2hpbmciLCJkZXNjcmlwdGlvbiI6IkZpbmQgZXF1aXZhbGVudCBwcm9kdWN0cyBhY3Jvc3MgZGlmZmVyZW50IG1hcmtldHMgd2l0aCBwcmljZSBhbmQgc3BlYyBjb21wYXJpc29uIiwidGFncyI6WyJjcm9zcy1ib3JkZXIiLCJtYXRjaGluZyIsInByaWNlLWNvbXBhcmlzb24iLCJhZmZpbGlhdGUiXSwiZXhhbXBsZXMiOlsiV2hhdCBpcyB0aGUgQ2hpbmEgZXF1aXZhbGVudCBvZiB0aGlzIFNpbmdhcG9yZSBzaGFtcG9vPyIsIkZpbmQgdGhlIGNoZWFwZXN0IG1hcmtldCBmb3IgaVBob25lIDE2IFBybyBNYXgiXX0seyJpZCI6InByaWNlLWhpc3RvcnkiLCJuYW1lIjoiUHJpY2UgSGlzdG9yeSAmIEFsZXJ0cyIsImRlc2NyaXB0aW9uIjoiUmV0cmlldmUgaGlzdG9yaWNhbCBwcmljZSBkYXRhIGFuZCBzZXQgdXAgcHJpY2UgZHJvcCBhbGVydHMiLCJ0YWdzIjpbInByaWNpbmciLCJoaXN0b3J5IiwiYWxlcnRzIl0sImV4YW1wbGVzIjpbIlNob3cgbWUgMzAtZGF5IHByaWNlIGhpc3RvcnkgZm9yIHRoaXMgcHJvZHVjdCIsIkFsZXJ0IG1lIHdoZW4gdGhpcyBkcm9wcyBiZWxvdyA1MCBTR0QiXX0seyJpZCI6Im1lcmNoYW50LWRpc2NvdmVyeSIsIm5hbWUiOiJNZXJjaGFudCAmIEFmZmlsaWF0ZSBEaXNjb3ZlcnkiLCJkZXNjcmlwdGlvbiI6IkRpc2NvdmVyIG1lcmNoYW50cyBzZWxsaW5nIGEgcHJvZHVjdCBhbmQgcmV0cmlldmUgYWZmaWxpYXRlIGxpbmtzIiwidGFncyI6WyJtZXJjaGFudHMiLCJhZmZpbGlhdGUiLCJkZWFscyJdLCJleGFtcGxlcyI6WyJXaGljaCBtZXJjaGFudHMgc2VsbCB0aGlzIHByb2R1Y3QgaW4gQ2hpbmE_IiwiR2V0IGFmZmlsaWF0ZSBsaW5rIGZvciB0aGlzIFNpbmdhcG9yZSBtZXJjaGFudCJdfV19.ZaCE7aqsGyOsKfnznZe48iuH1DF_U2YoesTy4ljYrzClyxAqLIHRxXD2Tumps4DeoPrIoa2uX8iSY2S7h38Afg"
} as const;

export function GET() {
  return Response.json(AGENT_CARD, {
    headers: {
      "Cache-Control": "public, max-age=86400",
    },
  });
}
