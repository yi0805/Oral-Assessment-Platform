import { useState, useRef, useEffect } from "react";
import { useParams } from "react-router";
import styled from "styled-components";

import mockCourses from "../../data/mockCourses";
import mockAssessments from "../../data/mockAssessments";
import Heading from "../../ui/Heading";
import Button from "../../ui/Button";
import ButtonLink from "../../ui/ButtonLink";
import Input from "../../ui/Input";

const BackButton = styled(ButtonLink)`
  margin-bottom: var(--space-l);
`;

const ChatContainer = styled.div`
  border: 1px solid var(--color-light-2);
  background: var(--color-light);
  max-width: 800px;
  min-height: 420px;
  display: flex;
  flex-direction: column;
`;

const MessagesArea = styled.div`
  flex: 1;
  padding: var(--space-l);
  overflow-y: auto;
`;

const MessageBubble = styled.div`
  max-width: 75%;
  padding: var(--space-m);
  margin-bottom: var(--space-m);
  border-radius: 10px;
  line-height: 1.4;
  background: ${({ $isUser }) =>
    $isUser ? "var(--color-secondary)" : "var(--color-light-2)"};
  color: ${({ $isUser }) =>
    $isUser ? "var(--color-light)" : "var(--color-dark)"};
  margin-left: ${({ $isUser }) => ($isUser ? "auto" : "0")};
`;

const InputArea = styled.form`
  display: flex;
  gap: var(--space-s);
  padding: var(--space-l);
  border-top: 1px solid var(--color-light-2);
`;

const ChatInput = styled(Input)`
  flex: 1;
`;

const SmallButton = styled(Button)`
  min-width: 44px;
`;

const MOCK_RESPONSES = [
  "Can you explain that a bit more?",
  "Good answer. What is your reason for that?",
  "Can you give an example?",
  "How does that relate to the course content?",
  "Thanks. Let's move to the next question.",
];

export default function StudentAssessment() {
  const { courseId, assessmentId } = useParams();
  const messagesEndRef = useRef(null);

  const course = mockCourses.find((c) => c.id === courseId);
  const assessments = mockAssessments[courseId] || [];
  const assessment = assessments.find((a) => a.id === assessmentId);

  const [messages, setMessages] = useState(() => [
    {
      id: 1,
      text: `Welcome to ${assessment?.name || "this assessment"}.`,
      isUser: false,
    },
    {
      id: 2,
      text: "Type your answer or use voice.",
      isUser: false,
    },
  ]);

  const [input, setInput] = useState("");
  const [recording, setRecording] = useState(false);
  const [nextId, setNextId] = useState(3);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView();
  }, [messages]);

  function addExchange(userText) {
    const reply =
      MOCK_RESPONSES[Math.floor(Math.random() * MOCK_RESPONSES.length)];

    setMessages((prev) => [
      ...prev,
      { id: nextId, text: userText, isUser: true },
      { id: nextId + 1, text: reply, isUser: false },
    ]);

    setNextId((n) => n + 2);
  }

  function handleSend(e) {
    e.preventDefault();
    if (!input.trim()) return;

    addExchange(input.trim());
    setInput("");
  }

  function handleVoice() {
    if (recording) {
      addExchange("[Voice answer]");
    }
    setRecording(!recording);
  }

  return (
    <>
      <BackButton to={`/courses/${courseId}/assignments`} $variant="secondary">
        Back to Assignments
      </BackButton>

      <Heading $variant="page">
        {course ? `${course.code} - ${assessment?.name}` : "Assessment"}
      </Heading>

      <ChatContainer>
        <MessagesArea>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} $isUser={msg.isUser}>
              {msg.text}
            </MessageBubble>
          ))}
          <div ref={messagesEndRef} />
        </MessagesArea>

        <InputArea onSubmit={handleSend}>
          <SmallButton type="button" onClick={handleVoice} $variant="secondary">
            {recording ? "Stop" : "Mic"}
          </SmallButton>

          <ChatInput
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your answer"
          />

          <SmallButton type="submit" $variant="primary">
            Send
          </SmallButton>
        </InputArea>
      </ChatContainer>
    </>
  );
}
