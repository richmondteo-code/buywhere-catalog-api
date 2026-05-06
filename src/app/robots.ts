import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
<<<<<<< HEAD
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/home/", "/PAP/", "/BUY/", "/v1/", "/v2/"],
      },
    ],
=======
    rules: {
      userAgent: "*",
      allow: "/",
    },
>>>>>>> a8194ee77 (fix(BUY-12731): use Cloud Run hostname + X-Forwarded-Host to fix 404 routing)
    sitemap: "https://buywhere.ai/sitemap.xml",
  };
}
