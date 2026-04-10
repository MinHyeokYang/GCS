import fs from "node:fs/promises";
import path from "node:path";
import pdfParse from "pdf-parse";

const sourceDir = process.argv[2] || "artifacts/research_pdfs";
const outputPath =
  process.argv[3] || "artifacts/ai_debate_landing/research_snippets.json";

const absSourceDir = path.resolve(sourceDir);
const absOutputPath = path.resolve(outputPath);

const files = (await fs.readdir(absSourceDir))
  .filter((name) => name.toLowerCase().endsWith(".pdf"))
  .sort((a, b) => a.localeCompare(b));

const results = [];

for (const file of files) {
  const fullPath = path.join(absSourceDir, file);
  const data = await fs.readFile(fullPath);
  const parsed = await pdfParse(data);

  const cleaned = (parsed.text || "")
    .replace(/\r/g, "")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  results.push({
    file,
    fullPath,
    pageCount: parsed.numpages ?? null,
    charCount: cleaned.length,
    snippet: cleaned.slice(0, 9000),
  });
}

await fs.mkdir(path.dirname(absOutputPath), { recursive: true });
await fs.writeFile(absOutputPath, JSON.stringify(results, null, 2), "utf8");

console.log(`Wrote ${results.length} files to ${absOutputPath}`);
