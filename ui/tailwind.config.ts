// tailwind.config.ts
// Workaround: import the ESM declaration file directly so TS can resolve it.
// Proper fix: set "moduleResolution": "nodenext" or "node16" in your tsconfig.json.
import type { Config } from "tailwindcss/dist/lib.d.mts";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",     // fine if you still have /pages
    "./lib/**/*.{js,ts,jsx,tsx}",           // utils/hooks if any
    "../shared/**/*.{js,ts,jsx,tsx,mdx}",   // monorepo/shared (if present)
    // if you bring in shadcn/ui or third-party UI that ships JSX:
    // "./node_modules/@tremor/**/*.{js,ts,jsx,tsx}",
  ],
  theme: { extend: {} },
  plugins: [],
};
export default config;
