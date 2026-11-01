# Orvina: feature list

## F1 · Ringkas Materi (summarize study material)
- Upload up to 10 files at once: PDF, PPTX, DOCX, TXT/MD, images, audio and video.
- Reads scanned pages, slide pictures and photos of the whiteboard with the vision model. Video is read through its speech and its keyframes.
- 4 summary styles:
  - Ringkas 1 halaman;
  - Catatan terstruktur;
  - Poin kunci + rumus + kode;
  - Latihan tanya jawab.
- 3 detail levels; output in Bahasa Indonesia, English or 中文 regardless of the source language.
- Math rendered as LaTeX (KaTeX), code blocks with syntax highlighting.
- **Important figures** taken from the files: diagrams, graphs and tables are picked, captioned and placed inline. Logos and decoration are filtered out.
- **Generated charts:** function curves and data plots drawn exactly from formulas in the material (no image AI, no executed AI code).
- Deadlines found in the material become schedule suggestions.
- Export to Markdown (zip with images) or HTML; "Ask in Forum" from any summary.
- "Di balik layar": shows which model did each step, with latency.

## F2 · Rekam & Transkrip (record and transcribe)
- Record in the browser or upload audio/video (up to 15 minutes).
- Or import a transcript you already have (.srt, .vtt, .txt from Zoom, Google Meet, Teams or YouTube).
- Transcript with timestamps, search, and download as .txt, .srt and .md.
- Translation into the other two languages.
- Meeting summary, decisions, and action items (who, what, when); dated items go to Jadwal in one click.

## F3 · Jadwal (schedule)
- Google Calendar connection (OAuth), or local mode with an .ics file and an add-to-Google link for each event.
- New events with reminders; the end time defaults to one hour after the start.
- Suggestions from summaries and meetings, accepted or dismissed with one tap.
- **Animated day atom:** the day's events orbit by time of day, and scrolling through the list moves the atom from day to day.

## F4 · Forum + Leaderboard
- Questions and answers with LaTeX, code, images, documents and video.
- Full-text search; filters (unanswered, answered, followed, subject); sorting.
- Similar questions shown while typing a new one, to avoid duplicates.
- AI tag suggestions and AI moderation (spam, abuse, off-topic).
- **"Minta petunjuk AI":** a hint or guiding question, never the final answer.
- Votes, best answer, follow a question.
- Points for asking, answering, upvotes and best answers.
- Weekly, monthly and all-time leaderboards with a subject filter and a "Kamu" row.

## Across the app
- **Dashboard "Minggu ini":** your week as an animated atom.
  - You are the nucleus and your days orbit around you.
  - Tap a day to zoom into it and see that day's events.
  - The dashboard also has stats, quick actions, questions for you, reminders, the top 5, and recent activity.
- **Accounts:** register, log in, and a 3-step onboarding (language, subjects, calendar).
- **Notifications:** upcoming events, new questions in your subjects, new answers, best answer, rank changes. Each kind can be switched off.
- **Perpustakaan:** all your summaries and transcripts, with search, filters, rename, download and delete.
- **Languages:** the whole UI in Bahasa Indonesia, English and 中文.
- **Themes:** light and dark mode, plus a "Kurangi animasi" (reduce motion) setting.
- **Accessibility and devices:** WCAG AA contrast, full keyboard use, screen-reader labels for the animated parts, and a usable layout down to 400 px phones.
- **Rules:** works on the free CPU tier and uses only the 4 competition models on ModelScope.

## Under the hood

| Part | Language |
|---|---|
| Animated web app | TypeScript + React + Motion |
| Server: API, accounts, forum, points, calendar, jobs, AI (4 ModelScope models, documents, figures, charts) | Python (FastAPI) |
| Database | SQL (SQLite, full-text search) |
| Contract between web and server | OpenAPI |
| One-image, one-process deployment on ModelScope Studio (free CPU) | Docker |
