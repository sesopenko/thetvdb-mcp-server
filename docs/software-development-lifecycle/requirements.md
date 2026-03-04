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

## Required tools (initial implementation scope)

| Purpose | MCP Tool | TVDB v4 Endpoint | Method | Key Inputs | Notes |
|---|---|---|---|---|---|
| Search for candidate series by show name and optional year | `tvdb_search_series(query, year?, limit, offset)` | `/search` | GET | `type=series`, `query` (or `q`), `year` (optional), `limit`, `offset` | Primary disambiguation step. `year` is optional. `limit` and `offset` are exposed so the LLM can page through results. |
| Fetch base series record **or** episode list, depending on params supplied | `tvdb_get_series_naming_bundle(seriesId, seasonType?, lang?)` | See endpoint selection below | GET | Path: `id`; optional `season-type`, `lang` | Single combined tool; endpoint chosen by which optional params are present (see below). |

#### `tvdb_get_series_naming_bundle` endpoint selection

This is **one tool** with two optional parameters. The endpoint called depends on which params are provided:

| `seasonType` | `lang` | Endpoint called | Purpose |
|---|---|---|---|
| omitted | omitted | `GET /series/{id}` | Fetch base series record to confirm canonical title and `firstAired` year. |
| provided | omitted | `GET /series/{id}/episodes/{seasonType}` | Fetch episode list for SxxExx mapping. Season-type controls ordering (e.g. `official`, `dvd`, `absolute`). |
| provided | provided | `GET /series/{id}/episodes/{seasonType}/{lang}` | Fetch episode list with localized titles. |

Both episode-list endpoints are **auto-paginated**: the tool fetches all pages internally and returns the complete episode list in a single MCP call.

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

