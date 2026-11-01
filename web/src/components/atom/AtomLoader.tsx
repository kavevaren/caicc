import { motion } from "framer-motion";

/**
 * AtomLoader — the logo's two ellipses counter-rotating (1.6 s) with a pulsing core.
 * DESIGN.md §3.6: replaces every spinner.
 */
export function AtomLoader({ size = 48 }: { size?: number }) {
  const s = size;
  return (
    <svg width={s} height={s} viewBox="0 0 512 512" role="img" aria-label="Memuat">
      <motion.g
        style={{ transformOrigin: "256px 256px" }}
        animate={{ rotate: 360 }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
      >
        <ellipse cx="256" cy="256" rx="170" ry="70" fill="none" stroke="var(--primary)" strokeWidth="24" transform="rotate(-30 256 256)" />
      </motion.g>
      <motion.g
        style={{ transformOrigin: "256px 256px" }}
        animate={{ rotate: -360 }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "linear" }}
      >
        <ellipse cx="256" cy="256" rx="170" ry="70" fill="none" stroke="var(--orbit)" strokeWidth="24" transform="rotate(30 256 256)" />
      </motion.g>
      <motion.circle
        cx="256"
        cy="256"
        r="28"
        fill="var(--accent)"
        animate={{ scale: [1, 1.25, 1] }}
        transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
        style={{ transformOrigin: "256px 256px" }}
      />
    </svg>
  );
}
