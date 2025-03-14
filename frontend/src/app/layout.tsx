import type { Metadata } from "next";
import "@cloudscape-design/global-styles/index.css";
import ClientLayout from "./layout.client";
import { FRONTEND_NAME } from "./consts";

export const metadata: Metadata = {
  title: FRONTEND_NAME,
  description: FRONTEND_NAME,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html>
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
