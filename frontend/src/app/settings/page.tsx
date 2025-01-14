"use client";
import * as React from "react";
import Form from "@cloudscape-design/components/form";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import FormField from "@cloudscape-design/components/form-field";
import Input from "@cloudscape-design/components/input";
import {
  BreadcrumbGroup,
  Popover,
  StatusIndicator,
} from "@cloudscape-design/components";

export default function Settings() {
  const [ak, setAk] = React.useState(window.localStorage.getItem("AK") ?? "");
  const [sk, setSk] = React.useState(window.localStorage.getItem("SK") ?? "");
  const [endpoint, setEndpoint] = React.useState(
    window.localStorage.getItem("ENDPOINT") ?? ""
  );

  return (
    <div>
      <BreadcrumbGroup
        items={[
          { text: "Bedrock CN", href: "/" },
          { text: "Settings", href: "/settings" },
        ]}
      />
      <form onSubmit={(e) => e.preventDefault()}>
        <Form
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Popover
                dismissButton={false}
                position="top"
                size="small"
                triggerType="custom"
                content={
                  <StatusIndicator type="success">Saved</StatusIndicator>
                }
              >
                <Button
                  onClick={() => {
                    window.localStorage.setItem("AK", ak);
                    window.localStorage.setItem("SK", sk);
                    window.localStorage.setItem("ENDPOINT", endpoint);
                  }}
                >
                  Save
                </Button>
              </Popover>
            </SpaceBetween>
          }
          header={<Header variant="h1">Settings</Header>}
        >
          <Container>
            <SpaceBetween direction="vertical" size="l">
              <FormField label="Access key">
                <Input
                  value={ak}
                  onChange={(e) => setAk(e.detail.value)}
                  type="password"
                />
              </FormField>
              <FormField label="Secret key">
                <Input
                  value={sk}
                  onChange={(e) => setSk(e.detail.value)}
                  type="password"
                />
              </FormField>
              <FormField label="Endpoint override (Optional)">
                <Input
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.detail.value)}
                />
              </FormField>
            </SpaceBetween>
          </Container>
        </Form>
      </form>
    </div>
  );
}
