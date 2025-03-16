"use client";
import { AppLayout, SideNavigation } from "@cloudscape-design/components";
import { I18nProvider } from "@cloudscape-design/components/i18n";
import messages from "@cloudscape-design/components/i18n/messages/all.en";
import { useState } from "react";
import { FRONTEND_NAME } from "./consts";

const LOCALE = "en";

export default function ClientLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [navigationOpen, setNavigationOpen] = useState(true);
  return (
    <I18nProvider locale={LOCALE} messages={[messages]}>
      <AppLayout
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        navigation={
          <SideNavigation
            header={{
              href: "/",
              text: FRONTEND_NAME,
            }}
            items={[
              {
                type: "section",
                text: "Playgrounds",
                items: [
                  {
                    type: "link",
                    text: `Chat / Text playground`,
                    href: `/chat`,
                  },
                ],
              },
              { type: "divider" },
              {
                type: "section",
                text: "Configurations",
                items: [
                  {
                    type: "link",
                    text: `Settings`,
                    href: `/settings`,
                  },
                ],
              },
            ]}
          />
        }
        content={children}
        toolsHide={true}
      />
    </I18nProvider>
  );
}
