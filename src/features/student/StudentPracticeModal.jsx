import styled from "styled-components";
import { useMemo, useState } from "react";

const StyledStudentPracticeModal = styled.div`
  position: fixed;
  inset: 0;
  background: rgba(var(--color-dark-rgb), 0.35);
  display: grid;
  place-items: center;
  padding: var(--space-4xl) var(--space-xl);
`;

const QuestionModal = styled.div`
  width: 100%;
  max-width: 80ch;
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 14px;
  padding: var(--space-4xl);
`;

const Title = styled.h2`
  font-size: var(--font-size-xl);
  color: var(--color-primary);
  margin-bottom: var(--space-m);
`;

const QuestionParagraph = styled.p`
  color: var(--color-dark-2);
  line-height: 1.5;
  margin-top: var(--space-m);
`;

const Input = styled.input`
  width: 100%;
  max-width: 65ch;
  padding: var(--space-m) var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  font-size: var(--font-size-default);
  margin-top: var(--space-xl);
`;

const ButtonContainer = styled.div`
  display: flex;
  gap: var(--space-m);
  align-items: center;
  justify-content: flex-end;
  margin-top: var(--space-2xl);
`;

const Button = styled.button`
  border: 0;
  border-radius: 10px;
  padding: var(--space-m) var(--space-2xl);
  font-weight: 700;
  cursor: pointer;
  color: var(--color-light);
  background: ${({ $variant }) =>
    $variant === "primary"
      ? "var(--color-secondary)"
      : "var(--color-tertiary)"};
`;

export default function StudentPracticeModal({
  isOpen,
  onClose,
  courseNumber,
}) {
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState(Array(10).fill(""));

  const questions = useMemo(() => {
    const c = courseNumber;
    return [
      `(${c}) Q1: How are you doing today?`,
      `(${c}) Q2: What for dinner?`,
      `(${c}) Q3: What is one thing you found interesting in the course?`,
      `(${c}) Q4: Test`,
      `(${c}) Q5: Test`,
      `(${c}) Q6: Test`,
      `(${c}) Q7: Test`,
      `(${c}) Q8: Test`,
      `(${c}) Q9: Test`,
      `(${c}) Q10: Test`,
    ];
  }, [courseNumber]);

  if (!isOpen) return null;

  const title = `AI practice (${questionIndex + 1}/10)`;
  const question = questions[questionIndex];
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
      <QuestionModal onClick={(e) => e.stopPropagation()}>
        <Title>{title}</Title>
        <QuestionParagraph>{question}</QuestionParagraph>

        <Input
          value={answer}
          onChange={(e) => setCurrentAnswer(e.target.value)}
          placeholder="Type your answer..."
        />

        <ButtonContainer>
          <Button
            type="button"
            $variant="primary"
            onClick={back}
            disabled={!canGoBack}
          >
            Back
          </Button>

          {!isLast ? (
            <Button type="button" $variant="primary" onClick={next}>
              Next
            </Button>
          ) : (
            <Button type="button" $variant="secondary" onClick={submit}>
              Submit
            </Button>
          )}
        </ButtonContainer>
      </QuestionModal>
    </StyledStudentPracticeModal>
  );
}
