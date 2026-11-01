# P4 · Web foundation + animated Dashboard (Sun 1 Nov – Mon 2 Nov) · lane C, can run in parallel with P2 and P3

**Read:** `_RULES.md`, `docs/design/DESIGN.md` (all of it), `docs/design/dashboard-mockup.html`, SPEC §8.1–§8.2, §8.9, §13 (iframe and proxy rules).
**Goal:** the React app shell, auth and onboarding, and the Dashboard with the full atom system. It runs against the MSW mocks first, then against the FastAPI server when that is ready. Work only inside `web/`.

> **Scope cut (see `_RULES.md`):**
> - Task 1: only the UI kit components the Must pages use.
> - Task 2: `watchJob(id)` polls every 2 s; no SSE and no stream ticket.
> - Task 3: `id` and `en` only; `zh` comes later if time allows.
> - Task 6: only `AtomLoader` plus one simple animation on the Dashboard; skip `WeekAtom` zoom, `DayAtom`, `StageAtom`, the keyboard controls and the hidden screen-reader list.
> - Task 7: hide the blocks for cut features (points ring, "Top 5 minggu ini", "Rekam kelas"); keep "7 hari ke depan", "Pertanyaan untuk kamu" (latest questions in the user's subjects) and "Aktivitas terakhir".
> - "Done when": skip the 5-second recording and Lighthouse; screenshots in light and 400 px are enough.

## Tasks
1. **Foundation:**
   - `tokens.css` (DESIGN §1.1, light + dark) and `global.css`;
   - `motion/tokens.ts`;
   - fonts via `@fontsource`;
   - the UI kit in `components/ui/` (DESIGN §5), each with a Vitest test.
2. **`lib/api.ts`:**
   - typed from `api-types.ts`;
   - **relative URLs only** (`api/...` resolved against the page), so the app works inside the Studio iframe at any path;
   - Bearer token in `localStorage` (wrapped in try/catch; an in-memory fallback if storage is blocked);
   - error JSON → i18n key;
   - 401 → logout;
   - `watchJob(id)`: fetch a stream ticket, open SSE; if no event arrives within 10 s or SSE errors, switch to polling `GET /api/jobs/{id}` every 2 s. Vitest covers the fallback.
3. **i18n:** `locales/{id,en,zh}.json` complete for everything built in this phase. A Vitest parity test fails if keys differ. ESLint `i18next/no-literal-string` is on.
4. **App shell** (DESIGN §2):
   - sidebar, header, drawer at ≤ 860 px;
   - page transition;
   - the health banner;
   - the error boundary with a translated message;
   - favicon D, tab titles.
5. **Login / Register / Onboarding** (DESIGN §4.1; SPEC §8.1):
   - field-level errors, including `terms_required`;
   - onboarding shown once, then `onboarding_done`.
6. **Atom system** (DESIGN §3.1–§3.4, §3.6): `useOrbit`, `project`, `WeekAtom` (idle, hover, scroll spin, dock, entrance), `DayAtom`, zoom with a `?day=` URL, `AtomLoader`, `StageAtom`. Then:
   - keyboard: arrows, Enter, Esc;
   - a hidden list for screen readers;
   - pause when off-screen;
   - reduced motion + the "Kurangi animasi" setting.
7. **Dashboard** (DESIGN §4.2) on `GET /api/dashboard`: every block, real data or an empty state; numbers count up; the points ring.

## Done when
- [ ] `npm run test`, `npm run lint`, `tsc --noEmit` and `npm run build` pass. The initial JS bundle is ≤ 250 KB gzip.
- [ ] Playwright screenshots of the Dashboard in light, dark and 400 px, **next to the mockup** at the same sizes.
- [ ] A 5-second screen recording of the zoom into a day and back.
- [ ] Lighthouse on the Dashboard: Performance ≥ 85, Accessibility ≥ 95.
- [ ] Reduced motion verified: no rotation, and the zoom is a crossfade.
- [ ] The built app opened **inside the test Studio page**: login works and the token survives a reload.
