# P5 · Feature pages, integrated end to end (Mon 2 Nov – Tue 3 Nov)

**Read:** `_RULES.md`, DESIGN §3.5, §3.6, §4.3–§4.8, SPEC §8.3–§8.8, §13.
**Goal:** every page works on the real FastAPI server, with the design and motion from DESIGN.md, deployed on the final Studio. Remove the MSW mocks from the production build.

## Pages
1. **Ringkas Materi:**
   - upload + options cards; the drop zone shows the `MAX_UPLOAD_MB` limit;
   - job → StageAtom via `watchJob` (SSE or polling);
   - result tabs, where figure include-toggles re-render with no model call;
   - export;
   - deadlines → Jadwal;
   - "Ask in Forum" prefill;
   - "Di balik layar".
2. **DocumentView** (`/library/:id`): the same tabs as the F1/F2 result, rename and delete.
3. **Rekam & Transkrip** (modes Rekam and Unggah only):
   - title + subtitle;
   - recording with a level ring; inside the iframe with the mic blocked, "Buka di tab baru";
   - one drop zone for media or a transcript file (.srt, .vtt, .txt);
   - with transcription disabled (health `whisper: disabled`): Rekam hidden, transcript files only, one line explaining why;
   - job + StageAtom;
   - result tabs;
   - action items → "Tambah ke Jadwal";
   - downloads .txt, .srt, .md;
   - the `media_too_long` message showing the real duration.
4. **Jadwal:**
   - sticky day atom + 30-day list synced by `IntersectionObserver`;
   - week ring;
   - direction-aware transitions;
   - the "Agenda baru" sheet (end = start + 1 h by default, end ≤ start rejected);
   - suggestions that fly into the atom;
   - Google card (connect in a new tab, refresh on focus);
   - .ics and template link per event.
5. **Forum:**
   - list with filters;
   - the empty state CTA "Ajukan pertanyaan" (no "Buka" button);
   - Ask: title counter 10–150, similar questions while typing (debounced 600 ms), write/preview with KaTeX, tags, attachments;
   - Detail: best answer first, animated votes, follow, owner edit/delete, the "Minta petunjuk AI" box.
6. **Leaderboard:** tabs, podium (numbers, no medals), layout-animated reorder, sticky "Kamu" row, "Cara dapat poin".
7. **Perpustakaan, Notifikasi, Profil:**
   - Profil has translated notification labels, "Kurangi animasi" and theme, followed subjects, and the password change.

## Done when
- [ ] Playwright e2e of the full loop passes on the Docker image: register → onboarding → summarize a PDF → ask in the Forum → answer as user 2 → best answer → deadline accepted into Jadwal.
- [ ] The same loop works with `ENABLE_TRANSCRIPTION=false`, plus an .srt import in Rekam & Transkrip.
- [ ] Screenshots of every page in light, dark and 400 px.
- [ ] **Every finding of the 30 Oct browser test is re-checked in the browser** and reported done / not done:
  - invalid-token banner;
  - forum ask opens and submits;
  - event saves;
  - no tracebacks;
  - onboarding shows;
  - the terms message;
  - the Transkrip page title;
  - no empty "Buka" button;
  - end time defaults to start + 1 h;
  - translated notification labels;
  - no mixed languages;
  - the Orvina brand, no emoji, the theme toggle.
- [ ] Deployed to the final Studio (free CPU, Public), with the seed loaded, and the loop clicked through **inside the Studio page**.

**Go / no-go, Tue 3 Nov 12:00.** If Dashboard + F1 + F2 + Jadwal do not work on the deployed Studio, stop and tell me. We then submit the old Streamlit app (folder `CAICC #2`) and only port bug fixes back.
