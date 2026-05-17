/**
 * markdown.ts — minimal markdown→block parser for legal docs. Avoids
 * pulling in a heavyweight runtime dep for a single viewer.
 *
 * Supported subset (sufficient for seeded legal docs):
 *   `## Heading`    → h2
 *   `### Heading`   → h3
 *   `- item`        → list (consecutive `- ` lines form one ul)
 *   blank line      → paragraph break
 *   everything else → paragraph (consecutive lines are joined with a space)
 */

export type MarkdownBlock =
  | { kind: "h2"; id: string; text: string }
  | { kind: "h3"; id: string; text: string }
  | { kind: "p"; id: string; text: string }
  | { kind: "list"; id: string; items: string[] };

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 80) || "section";
}

export function renderMarkdownBlocks(md: string): MarkdownBlock[] {
  const blocks: MarkdownBlock[] = [];
  const lines = md.replace(/\r/g, "").split("\n");
  let paraBuf: string[] = [];
  let listBuf: string[] = [];
  let counter = 0;
  const flushPara = () => {
    if (paraBuf.length === 0) return;
    const text = paraBuf.join(" ").trim();
    if (text) blocks.push({ kind: "p", id: `p-${++counter}`, text });
    paraBuf = [];
  };
  const flushList = () => {
    if (listBuf.length === 0) return;
    blocks.push({ kind: "list", id: `l-${++counter}`, items: listBuf.slice() });
    listBuf = [];
  };
  for (const raw of lines) {
    const line = raw.trim();
    if (line === "") {
      flushPara();
      flushList();
      continue;
    }
    if (line.startsWith("## ")) {
      flushPara();
      flushList();
      const text = line.slice(3).trim();
      blocks.push({ kind: "h2", id: slugify(text), text });
      continue;
    }
    if (line.startsWith("### ")) {
      flushPara();
      flushList();
      const text = line.slice(4).trim();
      blocks.push({ kind: "h3", id: slugify(text), text });
      continue;
    }
    if (line.startsWith("- ") || line.startsWith("* ")) {
      flushPara();
      listBuf.push(line.slice(2).trim());
      continue;
    }
    if (line.startsWith("# ")) {
      // Treat as h2 (h1 is the document title)
      flushPara();
      flushList();
      const text = line.slice(2).trim();
      blocks.push({ kind: "h2", id: slugify(text), text });
      continue;
    }
    flushList();
    paraBuf.push(line);
  }
  flushPara();
  flushList();
  return blocks;
}
