import { ThemeScope } from "@/lib/theme";

// Panel temasını (açık/koyu/sistem) bu sayfalara da uygula.
export default function ThemedLayout({ children }: { children: React.ReactNode }) {
  return <ThemeScope>{children}</ThemeScope>;
}
