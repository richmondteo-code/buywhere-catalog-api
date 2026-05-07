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

const contentDirectory = path.join(process.cwd(), "content", "compare");

type ContentFrontmatter = {
  title?: string;
  description?: string;
  slug?: string;
  category?: string;
  tags?: string[];
  schema_type?: string;
  published?: string;
  updated?: string;
};

type RouteParams = {
  params: {
    slug: string[];
  };
};

function parseContent(relativePath: string) {
  const fullPath = path.join(contentDirectory, relativePath);
  const source = fs.readFileSync(fullPath, "utf8");

  let data: matter.GrayMatterFile<string>["data"];
  let content: string;

  try {
    const parsed = matter(source);
    data = parsed.data;
    content = parsed.content;
  } catch {
    return null;
  }

  const frontmatter = data as ContentFrontmatter;
  const slug = relativePath.replace(/\.md$/, "").split(path.sep).join("/");
  const fallbackTitle = path.basename(relativePath, ".md");

  return {
    slug,
    title: frontmatter.title || fallbackTitle,
    description: frontmatter.description || "",
    category: frontmatter.category || "",
    tags: frontmatter.tags || [],
    schemaType: frontmatter.schema_type || "",
    published: frontmatter.published || "",
    updated: frontmatter.updated || "",
    body: content.trim(),
  };
}

function getAllContent() {
  try {
    return fs.readdirSync(contentDirectory, { withFileTypes: true })
      .flatMap((entry) => {
        if (entry.isDirectory()) return [];
        if (!entry.isFile() || !entry.name.endsWith(".md")) return [];
        return [entry.name];
      })
      .map(parseContent)
      .filter((doc) => doc !== null);
  } catch {
    return [];
  }
}

function getContentBySlug(slugParts: string[]) {
  const slug = slugParts.join("/");

  if (!slug || slugParts.some((part) => part === ".." || part.includes(path.sep))) {
    return null;
  }

  const docs = getAllContent();
  return docs.find((doc) => doc.slug === slug);
}

export async function generateStaticParams() {
  const docs = getAllContent();
  return docs.map((doc) => ({ slug: doc.slug.split("/") }));
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
      canonical: `https://buywhere.ai/compare/${doc.slug}`,
    },
    openGraph: {
      title: doc.title,
      description: doc.description,
      type: "website",
      url: `https://buywhere.ai/compare/${doc.slug}`,
      siteName: "BuyWhere",
    },
  };
}

function buildFaqSchema(frontmatter: ContentFrontmatter, body: string) {
  const faqBlocks: { name: string; acceptedAnswer: { "@type": string; text: string } }[] = [];
  const lines = body.split("\n");
  let currentQuestion = "";
  let currentAnswer = "";
  let inAnswer = false;

  for (const line of lines) {
    const questionMatch = line.match(/^## (.+)/);
    if (questionMatch) {
      if (currentQuestion && currentAnswer) {
        faqBlocks.push({
          name: currentQuestion.trim(),
          acceptedAnswer: { "@type": "Answer", text: currentAnswer.trim() },
        });
      }
      currentQuestion = questionMatch[1];
      currentAnswer = "";
      inAnswer = false;
    } else if (line.startsWith("BuyWhere") || line.startsWith("The BuyWhere") || line.startsWith("Yes") || line.startsWith("No") || line.startsWith("Both") || line.startsWith("Pricing") || line.startsWith("To get") || line.startsWith("The Smithery") || line.startsWith("For")) {
      if (currentQuestion && !inAnswer) {
        inAnswer = true;
        currentAnswer = line.replace(/^#+\s*/, "").trim();
      } else if (inAnswer) {
        currentAnswer += " " + line.trim();
      }
    } else if (inAnswer && line.trim() === "") {
      inAnswer = false;
    } else if (inAnswer && line.trim()) {
      currentAnswer += " " + line.trim();
    }
  }

  if (currentQuestion && currentAnswer) {
    faqBlocks.push({
      name: currentQuestion.trim(),
      acceptedAnswer: { "@type": "Answer", text: currentAnswer.trim() },
    });
  }

  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "@id": `https://buywhere.ai/compare/${frontmatter.slug}#faq`,
    mainEntity: faqBlocks,
  };
}

export default function CompareContentPage({ params }: RouteParams) {
  const doc = getContentBySlug(params.slug);

  if (!doc) {
    notFound();
  }

  const faqSchema = doc.schemaType === "FAQPage" ? buildFaqSchema(doc as unknown as ContentFrontmatter, doc.body) : null;

  const formatDate = (dateString: string) => {
    if (!dateString) return "";
    try {
      return new Intl.DateTimeFormat("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
        timeZone: "UTC",
      }).format(new Date(dateString));
    } catch {
      return dateString;
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      {faqSchema && (
        <Script id="faq-schema" type="application/ld+json" strategy="afterInteractive">
          {JSON.stringify(faqSchema)}
        </Script>
      )}
      <Nav />

      <main className="flex-1">
        <section className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 md:py-16">
            <Link href="/compare" className="mb-6 inline-flex text-sm font-medium text-indigo-600">
              ← Back to compare
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
              {doc.updated && (
                <span className="rounded-full bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
                  Updated: {formatDate(doc.updated)}
                </span>
              )}
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