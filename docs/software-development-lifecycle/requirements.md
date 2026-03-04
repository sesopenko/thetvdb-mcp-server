# requirements.md

## openapi spec

This system is built to use the following api: [https://thetvdb.github.io/v4-api/swagger.yml](https://thetvdb.github.io/v4-api/swagger.yml)

## First usage scenario

## Example real-world scenario (to guide MCP tool development)

### Context
- I rip/remux anime Blu-rays that I own into `.mkv` files.
- I need to organize files so **Emby** correctly identifies the show and episodes.
- My folder format is:

  /<show name> (<first aired year>)/Season XX/SXXEXX.mkv

- Emby uses **thetvdb.com** matching, primarily based on **show name + first-aired year** parsed from the folder name.
- I’m building an MCP server that exposes TVDB API endpoints as tools, so an LLM agent (via LibreChat + MCP) can help me:
  - confirm the correct TVDB series when there are naming collisions,
  - validate the “first aired” year used in the folder,
  - pull the correct episode list/ordering so my `SXXEXX` numbering is consistent.

### Typical flow I want to support
1. Given a folder name like:
   - `"/Monster (2004)/Season 01/S01E01.mkv"`
   parse:
   - `showName = "Monster"`
   - `year = 2004`

2. Search TVDB for the matching series:
   - call `/search` with `type=series`, `query=Monster`, `year=2004`
   - get candidate results (usually 1; sometimes multiple)

3. Select the correct candidate and confirm details:
   - call `/series/{id}` (and optionally `/series/{id}/extended`)
   - confirm the canonical title + firstAired year match what I’ll put in the folder name

4. Pull episode metadata for naming/verification:
   - call `/series/{id}/episodes/{season-type}` (optionally with language variant)
   - use returned episode list to ensure `Season XX` and `SXXEXX.mkv` numbering matches TVDB’s season ordering

### MCP implementation approach (initial)
- Keep MCP tools fairly general at first: expose tools that map closely to the TVDB endpoints needed for this flow.
- Authentication is handled transparently server-side; the LLM only calls data tools.
- Later, optionally add higher-level “one-shot” tools to reduce LLM steps/tokens.

## Authentication

Authentication is handled entirely by the MCP server. The LLM is not involved and has no tools related to authentication.

### How it works

On first use, the server calls `POST /login` with the configured `api_key` (and `pin` if provided) and caches the returned bearer token in memory. The token is attached automatically to every subsequent TVDB API request. If a request returns a 401, the server re-authenticates once and retries before surfacing an error.

### Token caching and expiry

The cached token is a JWT. Before every API call, the server must:

1. Decode the JWT (without verifying the signature — the `exp` claim is trusted from TVDB's own response) to read the `exp` field, which is a Unix timestamp (seconds since epoch).
2. Compare `exp` against the current time. If the token expires in **less than 10 minutes**, proactively fetch a fresh token via `POST /login` before proceeding with the API call.

This proactive refresh prevents in-flight requests from failing mid-operation due to token expiry. The 401-retry path remains as a fallback for unexpected expiry.

### Credential configuration

TVDB credentials are supplied via the `[tvdb]` section of `config.toml`:

```toml
[tvdb]
api_key = "your-api-key"   # required; obtain from thetvdb.com developer portal
# pin = "subscriber-pin"   # optional; only needed for subscriber content
```

- `api_key` is required.
- `pin` is optional; omit the key entirely if not a subscriber.

### Example Decoded token

```json
{
  "age": "",
  "apikey": "<redacted_string>",
  "community_supported": false,
  "exp": 1775228013,
  "gender": "",
  "hits_per_day": 100000000,
  "hits_per_month": 100000000,
  "id": "<redacted_integer_like_string>",
  "is_mod": false,
  "is_system_key": false,
  "is_trusted": false,
  "pin": null,
  "roles": [],
  "tenant": "tvdb",
  "uuid": ""
}
```

## Rate limiting

The MCP server must enforce a global rate limit of **1 TVDB API call per second** to avoid having access denied due to excessive requests.

### Requirements

- A single shared rate limiter governs all outbound TVDB API calls, regardless of which tool triggered them.
- Concurrent or simultaneous tool calls must queue through the same limiter — parallelism at the MCP layer must not translate to burst traffic at the TVDB API.
- If the limiter determines a call must wait, the server sleeps for the required duration before dispatching the request.
- The rate limit applies to every TVDB API call, including authentication (`POST /login`) and all paginated requests within a single tool call.

## Tool docstring clarity

All MCP tool docstrings must be written with LLM clarity as the primary goal. The docstring is the only information an LLM has when deciding how to call a tool, so ambiguity directly causes wasted tokens and incorrect calls.

### Rules

- Describe **what the tool does** and **when to use it** in the opening sentence.
- Every parameter must state: its type, whether it is required or optional, and what it does.
- Where a parameter accepts a fixed set of values, **list every valid value** with a plain-language explanation. Do not use "e.g." — enumerate completely.
- When a tool's behaviour changes depending on which optional parameters are provided, document each mode explicitly so the LLM can choose the right one without guessing.
- Avoid internal implementation terms (endpoint paths, HTTP methods, pagination mechanics). Describe outcomes, not mechanisms.

## Required tools (initial implementation scope)

### `tvdb_search_series`

**TVDB endpoint**: `GET /search`

Search TVDB for series matching a name, optionally filtered by first-aired year. Use this as the first step when you have a show name and need to find the correct TVDB series ID. Returns a list of candidate series; when multiple candidates are returned, use `firstAired` and other metadata to identify the correct one.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `query` | string | yes | The show name to search for. |
| `year` | integer | no | The four-digit year the series first aired. Providing this narrows results and resolves naming collisions between shows that share a title. |
| `limit` | integer | yes | Number of results to return per page. Use a small value (e.g. `5`) for an initial search; increase if the expected result is not in the first page. |
| `offset` | integer | yes | Zero-based index of the first result to return. Start at `0`; increment by `limit` to page through further results. |

### `tvdb_get_series`

**TVDB endpoint**: `GET /series/{id}`

Fetch the base record for a single series by its TVDB ID. Use this to confirm you have selected the correct show before fetching episode data — it returns the canonical title, `firstAired` year, overview, status, and other series-level metadata. Prefer this tool over re-running a search when you already have a series ID.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `seriesId` | integer | yes | The TVDB numeric series ID, as returned by `tvdb_search_series`. |

### `tvdb_get_series_naming_bundle`

**TVDB endpoints**: `GET /series/{id}`, `GET /series/{id}/episodes/{seasonType}`, `GET /series/{id}/episodes/{seasonType}/{lang}`

Fetch either the base series record or a complete episode list for a known TVDB series ID. The tool operates in two distinct modes determined by whether `seasonType` is provided:

**Mode 1 — series record** (`seasonType` omitted): Returns the canonical series title, `firstAired` year, status, and other series-level metadata. Use this to confirm you have the correct series before fetching episodes.

**Mode 2 — episode list** (`seasonType` provided): Returns every episode in the requested ordering. Use this to map season and episode numbers (`SxxExx`) to episode titles. All pages are fetched automatically; the full episode list is returned in a single call.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `seriesId` | integer | yes | The TVDB numeric series ID, as returned by `tvdb_search_series`. |
| `seasonType` | string | no | The episode ordering to use. Omit to fetch the base series record instead of episodes. When provided, must be one of the values below. |
| `lang` | string | no | A TVDB language code (e.g. `eng` for English, `jpn` for Japanese). When provided, episode titles are returned in the requested language. Only valid when `seasonType` is also provided; ignored otherwise. |

#### Valid `seasonType` values

| Value | Meaning | When to use |
|---|---|---|
| `official` | Standard broadcast order — episodes numbered as they originally aired on television. | Default choice for most series unless the user specifies otherwise. |
| `dvd` | DVD release order — episodes numbered as they appear on DVD, which may differ from broadcast order. | Use only when the user explicitly needs DVD ordering. |
| `absolute` | Absolute sequential numbering across all seasons with no season breaks (episode 1, 2, 3 … N). | Standard for anime and long-running series where fans refer to episodes by absolute number. Use for anime unless the user specifies otherwise. |
| `alternate` | A community-defined alternate ordering that differs from the official broadcast order. | Use only when the user explicitly requests alternate ordering. |
| `regional` | Region-specific ordering reflecting how the series aired in a particular country or market. | Use only when the user explicitly requests regional ordering. |

> **Note**: Verify that these values match the `season-type` enum in the TVDB v4 swagger spec during implementation. The swagger is the authoritative source.

### Deferred tools (out of scope for initial implementation)

The following tools are identified for potential future use but are **not implemented in the first pass**:

| Purpose | MCP Tool (suggested) | TVDB v4 Endpoint | Method |
|---|---|---|---|
| Fetch full/extended series record incl translations/episodes | `tvdb_get_series_extended(seriesId, meta, short)` | `/series/{id}/extended` | GET |
| Fetch series base record by slug | `tvdb_get_series_by_slug(slug)` | `/series/slug/{slug}` | GET |
| Fetch series title translations directly | `tvdb_get_series_translations(seriesId, language)` | `/series/{id}/translations/{language}` | GET |
| Fetch a single episode base record | `tvdb_get_episode(episodeId)` | `/episodes/{id}` | GET |
| Fetch a single episode extended record | `tvdb_get_episode_extended(episodeId)` | `/episodes/{id}/extended` | GET |
| Fetch a single episode translation | `tvdb_get_episode_translation(episodeId, language)` | `/episodes/{id}/translations/{language}` | GET |

