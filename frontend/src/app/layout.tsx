import type { Metadata } from "next";
import "./globals.css";
import "@cloudscape-design/global-styles/index.css";

export const metadata: Metadata = {
  title: "Bedrock CN",
  description: "Bedrock CN",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
