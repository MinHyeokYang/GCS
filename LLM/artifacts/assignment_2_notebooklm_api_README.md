# notebooklm-api

Unofficial TypeScript/JavaScript client and CLI for the Google NotebookLM API.

Fork of [`notebooklm`](https://www.npmjs.com/package/notebooklm) with extensive bug fixes (15+ RPC fixes) and new features (slide deck generation, artifact downloads). See [CHANGELOG.md](./CHANGELOG.md) for details.

## Install

```bash
npm install -g notebooklm-api
```

## Authentication

```bash
notebooklm login
```

Opens a browser to authenticate with your Google account. Credentials are stored locally in `~/.notebooklm/`.

## CLI Usage

### Notebooks

```bash
notebooklm create "My Research"           # Create notebook
notebooklm list                           # List all notebooks
```

### Sources

```bash
notebooklm source add-text <notebookId> -t "Title" -c "Content"
notebooklm source add-url <notebookId> <url>
notebooklm source list <notebookId>
notebooklm source delete <notebookId> <sourceId>
```

### Generate Content

```bash
# Reports
notebooklm generate report <notebookId> -p "Custom prompt" -w

# Slide decks
notebooklm generate slide-deck <notebookId> -p "Instructions" -f presenter -w

# Audio/video overviews
notebooklm generate audio <notebookId> -w
notebooklm generate video <notebookId> -w

# Check status
notebooklm generate status <notebookId> <artifactId>

# Download content
notebooklm generate download <notebookId> <artifactId> output.md
```

### Research

```bash
notebooklm research fast <notebookId> "research query"
notebooklm research deep <notebookId> "research query"
```

## Programmatic Usage

```typescript
import { NotebookLMClient } from 'notebooklm-api';

const client = await NotebookLMClient.fromStorage();

// Create notebook and add sources
const notebook = await client.notebooks.create('Research');
await client.sources.addText(notebook.id, 'Title', 'Content...');

// Generate report
const status = await client.artifacts.generateReport(notebook.id, {
  customPrompt: 'Analyze the key findings...'
});

// Wait and download
await client.artifacts.waitForGeneration(notebook.id, status.artifactId);
const content = await client.artifacts.downloadReport(notebook.id, status.artifactId);

// Generate slide deck
const slides = await client.artifacts.generateSlideDeck(notebook.id, {
  instructions: 'Create executive briefing...',
  format: 'presenter',
  length: 'default'
});
```

## Changelog

### 0.2.3 (2026-03-21)

#### Bug Fixes

- **Source import RPC params**: Fixed `importSources` (IMPORT_RESEARCH_SOURCES / `LBwxtb`) parameter structure from `[notebookId, [[url, title]]]` to `[null, [1], taskId, notebookId, [[null, null, [url, title], null*8, 2], ...]]`. Previous format caused Google to return null — sources discovered during research were never imported.
- **Source extraction double-nesting**: Fixed `parseResearchResult` source parsing — sources at `innerData[3]` are wrapped as `[[[url, title, snippet, 1], ...]]` (double-nested). Parser was iterating the outer array and passing the entire source list as a single entry to `parseResearchSource`. Added unwrapping logic.
- **taskId propagation**: `research()` now passes `taskId` to `importSources()` — required by the IMPORT_RESEARCH_SOURCES RPC.

### 0.2.2 (2026-03-21)

#### Bug Fixes

- **Research RPC params**: Fixed parameter structure for START_FAST_RESEARCH and START_DEEP_RESEARCH — was using flat `[notebookId, query, sourceType]`, corrected to `[[query, sourceType], null, 1, notebookId]` (fast) and `[null, [1], [query, sourceType], 5, notebookId]` (deep). Previous format caused Google to return null with error code `[3]`.
- **Poll RPC params**: Fixed POLL_RESEARCH params from `[notebookId, taskId]` to `[null, null, notebookId]`. Poll returns all tasks for the notebook.
- **Research result parsing**: Rewrote `parseResearchResult` to handle actual response structure `[[[taskId, innerData, ts, ts], ...]]` instead of expected flat `[statusCode, summary, sources]`. Now correctly finds task by ID, extracts sources/summary, and detects completion status.
- **Deep research timeout**: Increased default from 120s to 900s (15 min) — deep research takes 5-15 minutes. Fast research keeps 120s default.
- **CLI `--timeout` option**: Added `-t, --timeout <ms>` flag to `research web` command for custom timeout values.
- **Version string**: Fixed hardcoded `0.1.0` in CLI to match package version.

#### RPC Parameter Reference

| Method | ID | Params |
|--------|-----|--------|
| START_FAST_RESEARCH | `Ljjv0c` | `[[query, sourceType], null, 1, notebookId]` |
| START_DEEP_RESEARCH | `QA9ei` | `[null, [1], [query, sourceType], 5, notebookId]` |
| POLL_RESEARCH | `e3bVqc` | `[null, null, notebookId]` |

### 0.2.0 (2026-03-20)

Fork of [`notebooklm`](https://www.npmjs.com/package/notebooklm)`@0.1.1` by kaelen with extensive bug fixes and new features.

#### Bug Fixes

- **Source status parsing**: Sources always showed "processing" even when ready. The GET_NOTEBOOK response wraps status in `[null, statusCode]` array — added array traversal to extract the actual code.
- **Source list RPC method**: Changed from `hizoJc` (GET_SOURCE_FULLTEXT) to `rLM1Ne` (GET_NOTEBOOK) which actually returns sources.
- **Source ID parsing**: GET_NOTEBOOK wraps source IDs as `["uuid"]` arrays — added unwrapping logic in `parseSourceItem`.
- **Source list traversal**: `parseSourceList` now correctly finds sources at the right nesting level in the GET_NOTEBOOK response.
- **addText RPC params**: Fixed parameter format from flat `[notebookId, title, content]` to correct nested array structure per Google's batchexecute protocol.
- **addUrl RPC params**: Fixed parameter format for both regular URLs and YouTube URLs.
- **Source delete params**: Fixed to use triple-nested sourceId `[[[sourceId]]]`.
- **Generation status codes**: Fixed mapping — was `0=Pending, 1=InProgress, 2=Completed, 3=Error`, should be `1=Processing, 2=Pending, 3=Completed`.
- **Artifact status parsing**: Status is at `item[4]` in the LIST_ARTIFACTS response, not `item[3]`.
- **Artifact listing**: Added required `source-path=/notebook/{id}` URL parameter to `rpcCall` — without it, LIST_ARTIFACTS returns null.
- **getStatus method**: Replaced fake `GET_GENERATION_STATUS` RPC (doesn't exist) with LIST_ARTIFACTS + find by ID.
- **CREATE_ARTIFACT method ID**: Changed from `xpWGLf` to `R7cb6c`.
- **generateReport**: Complete rewrite — fetches source IDs from notebook and builds correct nested params with source ID references.
- **downloadReport**: Now reads `artifact.content` from LIST_ARTIFACTS response instead of returning empty string.

#### New Features

- **Slide deck generation**: Added `generateSlideDeck()` API method and `notebooklm generate slide-deck` CLI command with `--prompt`, `--format` (detailed/presenter), and `--length` (default/short) options.
- **Artifact download**: Added `notebooklm generate download <notebookId> <artifactId> <outputPath>` CLI command for downloading artifact content to files.
- **rpcCall source-path**: Added optional `sourcePath` parameter to `rpcCall` for methods that require notebook context.

#### RPC Method Reference

| Method | ID | Notes |
|--------|-----|-------|
| GET_NOTEBOOK | `rLM1Ne` | Returns notebook + sources |
| ADD_SOURCE | `izAoDd` | URL, text, YouTube |
| DELETE_SOURCE | `tGMBJ` | Triple-nested source ID |
| LIST_ARTIFACTS | `gArtLc` | Requires source-path |
| CREATE_ARTIFACT | `R7cb6c` | All artifact types |
| DELETE_ARTIFACT | `V5N4be` | |
| EXPORT_ARTIFACT | `Krh3pd` | To Docs/Sheets |
| IMPORT_RESEARCH_SOURCES | `LBwxtb` | Requires taskId |

## License

MIT
