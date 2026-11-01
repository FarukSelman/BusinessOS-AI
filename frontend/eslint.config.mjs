import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // toISOString() UTC'dir; Türkiye'de 00:00–03:00 arası tarihi bir gün geri kaydırır.
    files: ["**/*.{ts,tsx}"],
    ignores: ["lib/date.ts"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "CallExpression[callee.property.name=/^(slice|substring|split)$/][callee.object.callee.property.name='toISOString']",
          message: "Tarih için toISOString() kesmeyin (UTC). lib/date içindeki todayISO()/toISODate() kullanın.",
        },
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
