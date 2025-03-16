"use client";
import {
  ContentLayout,
  Container,
  Header,
  BreadcrumbGroup,
} from "@cloudscape-design/components";
import { FRONTEND_NAME } from "./consts";

export default function Home() {
  return (
    <div>
      <BreadcrumbGroup
        items={[
          { text: FRONTEND_NAME, href: "/" },
          { text: "Overview", href: "/" },
        ]}
      />
      <ContentLayout header={<Header>Overview</Header>}>
        <Container></Container>
      </ContentLayout>
    </div>
  );
}
