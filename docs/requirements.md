# requirements.md

## openapi spec

This system is built to use the following api: [https://thetvdb.github.io/v4-api/swagger.yml](https://thetvdb.github.io/v4-api/swagger.yml)

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

