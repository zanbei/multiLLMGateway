"use client";
import {
  ContentLayout,
  Container,
  Header,
  BreadcrumbGroup,
  FormField,
  PromptInput,
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
            header={<Header variant="h3">Generative AI chat</Header>}
            fitHeight
            disableContentPaddings
            footer={
              <FormField stretch>
                <PromptInput
                  value={prompt}
                  onChange={({ detail }) => setPrompt(detail.value)}
                  // onAction={onPromptSend}
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
