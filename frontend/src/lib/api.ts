import { SearchRequest, SearchResponse } from "./types";

export async function searchCandidates(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Search failed (${res.status}): ${text || res.statusText}`);
  }
  return res.json();
}
