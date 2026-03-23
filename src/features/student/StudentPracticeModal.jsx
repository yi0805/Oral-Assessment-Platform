import styled from "styled-components";
import { useMemo, useState } from "react";

import Input from "../../ui/Input";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import BodyText from "../../ui/BodyText";
import Button from "../../ui/Button";
import questions from "../../data/questions";

const StyledStudentPracticeModal = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(var(--color-dark-rgb), 0.35);
  display: grid;
  place-items: center;
`;

const ButtonContainer = styled.div`
  display: flex;
  gap: var(--space-m);
  margin-top: var(--space-2xl);
  align-items: center;
  justify-content: flex-end;
`;

export default function StudentPracticeModal({
  isOpen,
  onClose,
  courseNumber,
}) {
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState(Array(10).fill(""));

  const questionData = useMemo(() => questions, []);

  if (!isOpen) return null;

  const title = `AI practice (${questionIndex + 1}/10)`;
  const question = questionData[questionIndex];
  const answer = answers[questionIndex];

  const canGoBack = questionIndex > 0;
  const isLast = questionIndex === 9;

  const setCurrentAnswer = (value) => {
    setAnswers((ans) => ans.map((a, i) => (i === questionIndex ? value : a)));
  };

  function next() {
    setQuestionIndex((i) => Math.min(i + 1, 9));
  }

  function back() {
    setQuestionIndex((i) => Math.max(i - 1, 0));
  }

  function submit() {
    alert("Submitted!");
    onClose();
  }

  return (
    <StyledStudentPracticeModal onClick={onClose}>
      <ContentCard type="model" onClick={(e) => e.stopPropagation()}>
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

        <ButtonContainer>
          <Button type="button" onClick={back} disabled={!canGoBack}>
            Back
          </Button>

          {!isLast ? (
            <Button type="button" onClick={next}>
              Next
            </Button>
          ) : (
            <Button type="button" $variant="submit" onClick={submit}>
              Submit
            </Button>
          )}
        </ButtonContainer>
      </ContentCard>
    </StyledStudentPracticeModal>
  );
}
