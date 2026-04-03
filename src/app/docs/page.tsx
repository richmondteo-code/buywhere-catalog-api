"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DocsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/developers");
  }, [router]);

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
      <p className="text-gray-400">Redirecting to developer docs…</p>
    </div>
  );
}
