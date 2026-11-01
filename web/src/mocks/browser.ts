/**
 * MSW browser worker. Started from main.tsx in dev only, so `npm run dev`
 * runs the whole app shell without a server (P1 acceptance).
 */
import { setupWorker } from "msw/browser";

import { handlers } from "./handlers";

export const worker = setupWorker(...handlers);
