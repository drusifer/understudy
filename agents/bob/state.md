# Bob State

## Context
- 2026-10-22 session (Bob, coordinating; owner questions about the evening example):
  - "Box office" = `examples/mcp` (MCP server; `examples/mcp-remote` serves it over HTTP, but `examples/mcp/server.mjs:88` hardcodes 127.0.0.1 - no host option). The movie-picking one = `examples/evening` (`boxoffice.mjs` + `ratings.mjs` + `sketch.yaml`; Jev scores the `audience` question by reading `reviews`).
  - Ran evening with `--watch [--pause] --host 192.168.86.69 --port 4190`; it booked Crimson Static 20:00, F5/F6. Owner said the watch page was "not the one"; started the dashboard instead: `bobp make run ARGS="dashboard examples --port 4180 --host 192.168.86.69"` -> http://192.168.86.69:4180/ (may still be running; owner always wants servers bound to the NIC, not localhost).
  - Owner first asked for richer evening reviews, then changed direction: wants REAL data collection in the evening example, including Rotten Tomatoes scores. Asked for research only - do NOT sign up for anything.
  - Research summary given to owner: TMDB (free non-commercial key, attribution) for now-playing films + genres + user review text; OMDb (free key, 1,000/day) for Rotten Tomatoes % (plus IMDb/Metacritic) in its Ratings array. Official RT API is paid/application-only; scrapers are fragile/ToS risk. No free seat-map source anywhere; real showtimes maybe via Gracenote/TMS (`movies/showings`, US/CA, free-tier unclear) or MovieGlu (unclear). Proposed design: ratings server calls OMDb + TMDB; box office film list from TMDB now-playing; showtimes/seats stay simulated; env keys `OMDB_API_KEY`, `TMDB_API_KEY`; tests keep an offline fixture.
  - Test constraints if data changes: `tests/evening.test.js:92-104` asserts Night Shift tomato 82, 3-5 reviews, horror both >=70 and <70, non-horror both >90 and <=90; Jev doubles in `tests/jevScore.test.js`, `tests/dashboardRun.test.js`, `tests/browser/dashboard.test.js` match /scream|best scare/ in reviews.
- Earlier (2026-10-17): test-pyramid guidance added to `agents/AGENTS.md` #2 and `agents/skills/test-runner/SKILL.md`; dashboard CRT fix done and reviewed.
- Uncommitted working tree (none mine this session): agents/AGENTS.md, CHAT.diagram.md, CHAT.md, bob/morpheus/mouse/neo state.md, skills/test-runner/SKILL.md, examples/http/server.mjs, src/dashboard/{page.css,page.mjs,theme-professional.css,theme-starship.css}, tests/{dashboard.test.js,browser/dashboard.test.js}; untracked `data/` (household CSVs - keep out of git).

## Current Task
- Status: Paused awaiting owner decision (research delivered).
### Progress
- [x] /init, answered how to run box office / evening examples.
- [x] Ran evening live on the NIC; started dashboard on 192.168.86.69:4180.
- [x] Researched free real movie data sources and summarized for owner.
- [ ] Owner obtains TMDB + OMDb keys and confirms the design.
- [ ] Plan + implement real-data evening example (likely Tier 2 story via Cypher/Morpheus, then Neo *impl).

## Next Steps
1. Read the last messages of `agents/CHAT.md`; ask the owner (one question at a time) whether they have the TMDB and OMDb keys and accept the design above (live data for runs, offline fixture for tests, simulated showtimes/seats).
2. On yes: route as Tier 2 - `@Cypher`/`@Morpheus` combined story+arch for "evening plays real films", then Neo `*impl`. Touch `examples/evening/ratings.mjs` (OMDb tomato + TMDB reviews), `examples/evening/boxoffice.mjs` (TMDB now_playing -> film list, simulated showings/seats), `examples/evening/sketch.yaml` (gates may need retuning to real scores), and the tests listed in Context.
3. Never commit API keys; use env vars. Bind any served page to 192.168.86.69 (or --host per owner), not localhost.
4. Separate concern still open: Sprint 16 (Monarch+Amex ETL) planning per `agents/morpheus/state.md` Next Steps.
