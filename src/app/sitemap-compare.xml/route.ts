import { getCompareSitemapEntries, renderUrlSet, buildSitemapResponse } from "@/lib/sitemaps";

export const dynamic = "force-static";
export const revalidate = 3600;

export async function GET(): Promise<Response> {
  const entries = getCompareSitemapEntries();
  const xml = renderUrlSet(entries);
  return buildSitemapResponse(xml);
}