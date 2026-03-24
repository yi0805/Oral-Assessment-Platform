import styled from "styled-components";
import { useState } from "react";

import Input from "../../ui/Input";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import BodyText from "../../ui/BodyText";
import Button from "../../ui/Button";
import ActionsContainer from "../../ui/ActionsContainer";
import questions from "../../data/questions";

const Overlay = styled.div`
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(var(--color-dark-rgb), 0.35);
  display: grid;
  place-items: center;
`;

export default function StudentPracticeModal({
  isOpen,
  onClose,
  courseNumber,
}) {
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState(Array(questions.length).fill(""));

  if (!isOpen) return null;

  const title = `AI practice (${questionIndex + 1}/${questions.length})`;
  const question = questions[questionIndex];
  const answer = answers[questionIndex];

  const canGoBack = questionIndex > 0;
  const isLast = questionIndex === questions.length - 1;

  const setCurrentAnswer = (value) => {
    setAnswers((ans) => ans.map((a, i) => (i === questionIndex ? value : a)));
  };

  function next() {
    setQuestionIndex((i) => Math.min(i + 1, questions.length - 1));
  }

  function back() {
    setQuestionIndex((i) => Math.max(i - 1, 0));
  }

  function submit() {
    alert("Submitted!");
    onClose();
  }

  return (
    <Overlay onClick={onClose}>
      <ContentCard $variant="modal" onClick={(e) => e.stopPropagation()}>
        <Heading>{title}</Heading>
        <BodyText>Course Number: {courseNumber}</BodyText>
        <BodyText>{question}</BodyText>

        <Input
          type="text"
          $variant="modal"
          value={answer}
          onChange={(e) => setCurrentAnswer(e.target.value)}
          placeholder="Type your answer..."
        />

        <ActionsContainer $variant="end">
          <Button $variant="secondary" onClick={back} disabled={!canGoBack}>
            Back
          </Button>

          {!isLast ? (
            <Button onClick={next}>Next</Button>
          ) : (
            <Button $variant="tertiary" onClick={submit}>
              Submit
            </Button>
          )}
        </ActionsContainer>
      </ContentCard>
    </Overlay>
  );
}
