import { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/home/", "/PAP/", "/BUY/", "/v1/", "/v2/"],
      },
    ],
    sitemap: "https://buywhere.ai/sitemap.xml",
  };
}
