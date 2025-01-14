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
import { INITIAL_MESSAGES, Message } from "./config";
import {
  BedrockRuntimeClient,
  ConverseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";

const modelId = "anthropic.claude-3-haiku-20240307-v1:0";

export default function Chat() {
  const [prompt, setPrompt] = useState("");
  const [promptDisabled, setPromptDisabled] = useState(false);
  const [messages, setMessages] = useState([] as Message[]);

  async function converse(messages: Message[]) {
    const bedrock = new BedrockRuntimeClient({
      region: "us-east-1",
      credentials: {
        accessKeyId: window.localStorage.getItem("AK")!,
        secretAccessKey: window.localStorage.getItem("SK")!,
      },
    });

    const response = await bedrock.send(
      new ConverseStreamCommand({
        modelId,
        messages: messages
          .slice(0, -1)
          .filter((m) => m.type == "chat-bubble")
          .map((message) => ({
            role: message.authorId == "user" ? "user" : "assistant",
            content: [{ text: message.content!.toString() }],
          })),
      })
    );

    for await (const event of response.stream!) {
      const chunk = event.contentBlockDelta;
      if (chunk?.delta?.text) {
        const message = chunk.delta.text.toString();
        if (message) {
          messages.at(-1)!.content += message;
          setMessages(messages);
        }
      }
    }
  }

  function onPromptSend() {
    if (prompt) {
      const newMessages = [
        ...messages,
        { type: "chat-bubble", authorId: "user", content: prompt },
        {
          type: "chat-bubble",
          authorId: "gen-ai",
          content: "",
          avatarLoading: true,
        },
      ] as Message[];
      setMessages(newMessages);
      setPrompt("");
      setPromptDisabled(true);

      converse(newMessages).finally(() => {
        setPromptDisabled(false);
        const msg = newMessages.at(-1)!;
        if (msg.type == "chat-bubble") msg.avatarLoading = false;
        setMessages(newMessages);
      });
    }
  }

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
                  onClick={() => {
                    setPromptDisabled(true);
                    setMessages(INITIAL_MESSAGES.slice());
                  }}
                >
                  Examples
                </Button>
                <Button
                  ariaLabel="Clear"
                  iconName="remove"
                  variant="icon"
                  onClick={() => {
                    setMessages([]);
                    setPromptDisabled(false);
                  }}
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
                  onAction={onPromptSend}
                  disabled={promptDisabled}
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
