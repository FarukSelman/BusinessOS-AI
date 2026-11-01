import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// toISOString() UTC'dir; Türkiye'de 00:00–03:00 arası tarihi bir gün geri kaydırır.
const noIsoDateSlicing = {
  selector:
    "CallExpression[callee.property.name=/^(slice|substring|split)$/][callee.object.callee.property.name='toISOString']",
  message: "Tarih için toISOString() kesmeyin (UTC). lib/date içindeki todayISO()/toISODate() kullanın.",
};

// Panelde ham Tailwind renkleri (bg-red-50, text-emerald-400…) karanlık/aydınlık temaya uymaz;
// globals.css token'ları kullanılır: text-success, bg-danger-soft, border-border, text-ink-muted…
const RAW_COLOR =
  "(^|[ :])(bg|text|border|border-[trblxy]|ring|divide|fill|stroke|from|to|via|outline|placeholder|decoration)-(red|rose|pink|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|slate|gray|zinc|neutral|stone)-[0-9]";
const rawColorMessage =
  "Ham Tailwind rengi temaya uymaz. Token kullanın: text-success/warning/danger/info/violet, bg-*-soft, border-*-border, bg-*-solid, text-ink(-muted), bg-surface(-elevated), border-border.";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["**/*.{ts,tsx}"],
    ignores: ["lib/date.ts"],
    rules: { "no-restricted-syntax": ["error", noIsoDateSlicing] },
  },
  {
    // Temalı sayfalar. Aynı kural adı önceki bloğu ezdiği için tarih kuralı burada da tekrar edilir.
    files: ["app/(dashboard)/**/*.tsx", "app/admin/**/*.tsx", "app/invitations/**/*.tsx", "components/**/*.tsx"],
    ignores: ["components/auth/**"],
    rules: {
      "no-restricted-syntax": [
        "error",
        noIsoDateSlicing,
        { selector: `Literal[value=/${RAW_COLOR}/]`, message: rawColorMessage },
        { selector: `TemplateElement[value.raw=/${RAW_COLOR}/]`, message: rawColorMessage },
      ],
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
