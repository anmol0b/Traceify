import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/Providers";
import { SiteFooter, SiteHeader } from "@/components/SiteChrome";
import { cn } from "@/lib/utils";
import "./globals.css";

const sans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const mono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Traceify — Public profile intelligence",
  description: "Load any public X profile and have a grounded AI conversation about the person, backed by semantic search over their tweets.",
};

export const viewport: Viewport = {
  themeColor: "#000000",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={cn("dark h-full scroll-smooth antialiased", sans.variable, mono.variable)}>
      <body className="flex min-h-full flex-col font-sans">
        <Providers>
          <SiteHeader />
          <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col md:border-x">{children}</main>
          <SiteFooter />
        </Providers>
      </body>
    </html>
  );
}
