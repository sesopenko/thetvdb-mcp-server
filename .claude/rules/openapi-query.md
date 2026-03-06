# Claude Code Instructions

## OpenAPI Spec Access

When you need information from an OpenAPI/Swagger spec reachable via URL:

- **MUST** use the `mcp__openapi-query__*` tools (`list_paths`, `get_path_item`,
  `get_operation`) to query the spec.
- **MUST NOT** fetch the raw spec file into context via `WebFetch`, `Read`, or any
  other tool that loads the full document.

Spec files are large. Loading them whole causes attention degradation and unnecessary
token cost. The openapi-query tools return only the relevant fragment.

### Correct usage

1. `mcp__openapi-query__list_paths` — discover available paths.
2. `mcp__openapi-query__get_path_item` — get all operations for a specific path.
3. `mcp__openapi-query__get_operation` — get a single operation (preferred when the
   method and path are already known).
