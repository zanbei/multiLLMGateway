"use client";
import {
  ContentLayout,
  Container,
  Header,
  BreadcrumbGroup,
  FormField,
  PromptInput,
  Button,
} from "@cloudscape-design/components";
import { useState } from "react";
import Messages from "./messages";
import { ScrollableContainer } from "./common";
import { INITIAL_MESSAGES } from "./config";

export default function Chat() {
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState(INITIAL_MESSAGES);

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <BreadcrumbGroup
        items={[
          { text: "Bedrock CN", href: "/" },
          { text: "Chat / Text playground", href: "/chat" },
        ]}
      />
      <ContentLayout>
        <div style={{ height: "100%" }}>
          <Container
            header={
              <div style={{ display: "flex" }}>
                <Header variant="h3">Generative AI chat</Header>
                <Button
                  ariaLabel="Load examples"
                  iconName="folder"
                  variant="icon"
                  onClick={() => setMessages(INITIAL_MESSAGES.slice())}
                >
                  Examples
                </Button>
                <Button
                  ariaLabel="Clear"
                  iconName="remove"
                  variant="icon"
                  onClick={() => setMessages([])}
                ></Button>
              </div>
            }
            fitHeight
            disableContentPaddings
            footer={
              <FormField stretch>
                <PromptInput
                  value={prompt}
                  onChange={({ detail }) => setPrompt(detail.value)}
                  // onAction={onPromptSend}
                  actionButtonAriaLabel="Send"
                  actionButtonIconName="send"
                  placeholder="Ask a question"
                  autoFocus
                />
              </FormField>
            }
          >
            <ScrollableContainer>
              <Messages messages={messages} />
            </ScrollableContainer>
          </Container>
        </div>
      </ContentLayout>
    </div>
  );
}
