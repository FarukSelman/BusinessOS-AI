import type { Metadata } from "next";
import { Sora, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemedToaster } from "@/components/providers/themed-toaster";
import { ThemeProvider, themeInitScript } from "@/lib/theme";


const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "İşletme Yönetim Platformu",
  description: "KOBİ'ler için çok ajanlı yapay zekâ destekli işletme yönetim platformu",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="tr"
      className={`${sora.variable} ${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
      // Tema script'i "dark" sınıfını React'ten önce ekler; sunucu HTML'iyle farkı beklenen bir fark.
      suppressHydrationWarning
    >
      <head>
        {/* İlk boyamadan önce temayı uygula: önce aydınlık açılıp kararma (flaş) olmasın. */}
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          {children}
          <ThemedToaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
