import { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://buywhere.ai";
  const now = new Date();

  const routes = [
    { url: "/", priority: 1.0, changeFrequency: "weekly" as const },
    { url: "/developers", priority: 0.9, changeFrequency: "weekly" as const },
    { url: "/use-cases", priority: 0.8, changeFrequency: "monthly" as const },
    { url: "/pricing", priority: 0.8, changeFrequency: "monthly" as const },
    { url: "/about", priority: 0.6, changeFrequency: "monthly" as const },
    { url: "/contact", priority: 0.5, changeFrequency: "monthly" as const },
    { url: "/privacy", priority: 0.3, changeFrequency: "yearly" as const },
    { url: "/terms", priority: 0.3, changeFrequency: "yearly" as const },
  ];

  return routes.map(({ url, priority, changeFrequency }) => ({
    url: `${base}${url}`,
    lastModified: now,
    changeFrequency,
    priority,
  }));
}
