import Link from "next/link";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import fs from "node:fs";
import path from "node:path";
import matter from "gray-matter";
import Script from "next/script";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";

const directoryContentDir = path.join(process.cwd(), "content", "directory");

type ContentFrontmatter = {
  title?: string;
  description?: string;
  slug?: string;
  category?: string;
  tags?: string[];
  published?: string;
};

type RouteParams = {
  params: {
    slug: string[];
  };
};

function getAllDirectoryContent() {
  try {
    return fs.readdirSync(directoryContentDir, { withFileTypes: true })
      .filter((entry) => entry.isFile() && entry.name.endsWith(".md"))
      .map((entry) => entry.name.replace(".md", ""))
      .filter((slug) => slug && !slug.includes("/"))
      .map((slug) => {
        try {
          const fullPath = path.join(directoryContentDir, `${slug}.md`);
          const source = fs.readFileSync(fullPath, "utf8");
          const parsed = matter(source);
          const fm = parsed.data as ContentFrontmatter;
          return {
            slug: fm.slug || slug,
            title: fm.title || slug,
            description: fm.description || "",
            category: fm.category || "",
            tags: fm.tags || [],
            published: fm.published || "",
            body: parsed.content.trim(),
          };
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  } catch {
    return [];
  }
}

function getContentBySlug(slugParts: string[]) {
  const slug = slugParts.join("/");

  if (!slug || slugParts.some((part) => part === ".." || part.includes(path.sep))) {
    return null;
  }

  const allContent = getAllDirectoryContent();
  return allContent.find((doc) => doc && doc.slug === slug) || null;
}

export async function generateStaticParams() {
  const docs = getAllDirectoryContent();
  return docs.map((doc) => ({ slug: [doc!.slug] })).filter(Boolean);
}

export async function generateMetadata({ params }: RouteParams): Promise<Metadata> {
  const doc = getContentBySlug(params.slug);

  if (!doc) {
    return {};
  }

  return {
    title: doc.title,
    description: doc.description,
    alternates: {
      canonical: `https://buywhere.ai/directory/${doc.slug}`,
    },
    openGraph: {
      title: doc.title,
      description: doc.description,
      type: "website",
      url: `https://buywhere.ai/directory/${doc.slug}`,
      siteName: "BuyWhere",
    },
  };
}

function buildSoftwareAppSchema(doc: NonNullable<ReturnType<typeof getContentBySlug>>) {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "@id": `https://buywhere.ai/directory/${doc.slug}#software`,
    name: doc.title,
    description: doc.description,
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Any (MCP-compatible client)",
    url: "https://buywhere.ai",
    sameAs: [
      "https://github.com/BuyWhere/buywhere-mcp",
      "https://www.npmjs.com/package/@buywhere/mcp-server",
      "https://smithery.ai/server/buywhere",
    ],
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
      description: "Free tier: 1,000 API calls/month",
    },
    publisher: {
      "@type": "Organization",
      "@id": "https://buywhere.ai/#organization",
      name: "BuyWhere",
      url: "https://buywhere.ai",
    },
  };
}

export default function DirectoryContentPage({ params }: RouteParams) {
  const doc = getContentBySlug(params.slug);

  if (!doc) {
    notFound();
  }

  const softwareSchema = buildSoftwareAppSchema(doc);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Script id="software-schema" type="application/ld+json" strategy="afterInteractive">
        {JSON.stringify(softwareSchema)}
      </Script>
      <Nav />

      <main className="flex-1">
        <section className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 md:py-16">
            <Link href="/directory" className="mb-6 inline-flex text-sm font-medium text-indigo-600">
              ← Browse all directories
            </Link>
            <h1 className="mb-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              {doc.title}
            </h1>
            <div className="mb-4 flex flex-wrap gap-2 text-sm text-slate-500">
              {doc.category && (
                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
                  {doc.category}
                </span>
              )}
              {doc.tags.slice(0, 5).map((tag) => (
                <span key={tag} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                  {tag}
                </span>
              ))}
            </div>
            {doc.description && (
              <p className="max-w-3xl text-lg leading-8 text-slate-600">{doc.description}</p>
            )}
          </div>
        </section>

        <section className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
          <article className="overflow-hidden rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm sm:p-10">
            <div className="blog-prose">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => (
                    <h1 className="mt-10 text-3xl font-bold tracking-tight text-slate-900 first:mt-0">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="mt-10 text-2xl font-semibold tracking-tight text-slate-900">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="mt-8 text-xl font-semibold text-slate-900">{children}</h3>
                  ),
                  p: ({ children }) => (
                    <p className="mt-5 text-base leading-8 text-slate-700">{children}</p>
                  ),
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      className="font-medium text-indigo-600 underline decoration-indigo-200 underline-offset-4"
                    >
                      {children}
                    </a>
                  ),
                  ul: ({ children }) => (
                    <ul className="mt-5 list-disc space-y-3 pl-6 text-base leading-8 text-slate-700">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="mt-5 list-decimal space-y-3 pl-6 text-base leading-8 text-slate-700">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => <li>{children}</li>,
                  blockquote: ({ children }) => (
                    <blockquote className="mt-6 rounded-r-2xl border-l-4 border-indigo-500 bg-indigo-50/70 px-5 py-4 text-slate-700">
                      {children}
                    </blockquote>
                  ),
                  hr: () => <hr className="my-8 border-slate-200" />,
                  code: ({ className, children }) => (
                    <code
                      className={
                        className
                          ? `${className} font-mono text-sm text-slate-100`
                          : "rounded bg-slate-100 px-1.5 py-0.5 font-mono text-[0.95em] text-slate-800"
                      }
                    >
                      {children}
                    </code>
                  ),
                  pre: ({ children }) => (
                    <pre className="mt-6 overflow-x-auto rounded-2xl bg-slate-950 p-5 text-sm leading-7 text-slate-100">
                      {children}
                    </pre>
                  ),
                  table: ({ children }) => (
                    <div className="mt-6 overflow-x-auto">
                      <table className="min-w-full border-collapse overflow-hidden rounded-2xl border border-slate-200 text-left text-sm">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => <thead className="bg-slate-100 text-slate-700">{children}</thead>,
                  tbody: ({ children }) => <tbody className="divide-y divide-slate-200 bg-white">{children}</tbody>,
                  th: ({ children }) => <th className="px-4 py-3 font-semibold">{children}</th>,
                  td: ({ children }) => <td className="px-4 py-3 align-top text-slate-600">{children}</td>,
                }}
              >
                {doc.body}
              </ReactMarkdown>
            </div>
          </article>
        </section>
      </main>

      <Footer />
    </div>
  );
}