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
- Keep MCP tools fairly general at first:
  - expose tools that map closely to the TVDB endpoints needed for this flow
  - handle `/login` token caching/refresh server-side
- Later, optionally add higher-level “one-shot” tools to reduce LLM steps/tokens.

## first required api endpoints

| Purpose | MCP Tool (suggested) | TVDB v4 Endpoint | Method | Key Inputs | Notes |
|---|---|---|---|---|---|
| Authenticate / get token (cached + refreshed server-side) | (internal to all tools) | `/login` | POST | `apikey` (and optional `pin`) | Token is required for the rest; cache it in the MCP server. |
| Search for candidate series by show name + year | `tvdb_search_series(query, year, limit)` | `/search` | GET | `type=series`, `query` (or `q`), `year`, `limit`, `offset` | Primary disambiguation step (name + year). Return compact candidate list. |
| Fetch canonical/base series record for a chosen seriesId | `tvdb_get_series_naming_bundle(seriesId, ...)` | `/series/{id}` | GET | Path: `id` | Use to confirm canonical title and `firstAired` year for folder naming. |
| Fetch episode list for a chosen seriesId under a specific season order | `tvdb_get_series_naming_bundle(seriesId, seasonType, ...)` | `/series/{id}/episodes/{season-type}` | GET | Path: `id`, `season-type` | Main endpoint for building SxxExx mapping. Season-type controls ordering. |
| Fetch episode list with localized titles | `tvdb_get_series_naming_bundle(seriesId, seasonType, lang)` | `/series/{id}/episodes/{season-type}/{lang}` | GET | Path: `id`, `season-type`, `lang` | Use if you want non-default language episode titles. |
| (Optional) Fetch full/extended series record incl translations/episodes | `tvdb_get_series_extended(seriesId, meta, short)` | `/series/{id}/extended` | GET | Path: `id`; Query: `meta=translations|episodes`, `short=true|false` | Often avoid unless you need extra fields; can be large. |
| (Optional) Fetch series base record by slug | `tvdb_get_series_by_slug(slug)` | `/series/slug/{slug}` | GET | Path: `slug` | Only needed if you store/receive slugs; not required for name+year flow. |
| (Optional) Fetch series title translations directly | `tvdb_get_series_translations(seriesId, language)` | `/series/{id}/translations/{language}` | GET | Path: `id`, `language` | Lightweight way to get localized series titles without `/extended`. |
| (Optional) Fetch a single episode base record (if you already have episodeId) | `tvdb_get_episode(episodeId)` | `/episodes/{id}` | GET | Path: `id` | Not needed for bulk naming if you already pull episode lists from the series endpoint. |
| (Optional) Fetch a single episode extended record (if you already have episodeId) | `tvdb_get_episode_extended(episodeId)` | `/episodes/{id}/extended` | GET | Path: `id` | Only if you need extra per-episode metadata not in the episode list response. |
| (Optional) Fetch a single episode translation | `tvdb_get_episode_translation(episodeId, language)` | `/episodes/{id}/translations/{language}` | GET | Path: `id`, `language` | Only if you need per-episode localized titles and aren’t using the series episodes `{lang}` endpoint. |

