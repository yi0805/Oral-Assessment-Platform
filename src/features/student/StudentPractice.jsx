import { useState } from "react";
import styled from "styled-components";

import StudentPracticeModal from "./StudentPracticeModal";

const StyledStudentPractice = styled.div`
  max-width: 56rem;
  background: var(--color-light);
  border: 1px solid var(--color-light-2);
  border-radius: 14px;
  padding: var(--space-4xl);
`;

const Title = styled.h1`
  font-size: var(--font-size-xxl);
  color: var(--color-primary);
  margin-bottom: var(--space-xl);
`;

const CourseContainer = styled.div`
  display: flex;
  gap: var(--space-m);
  align-items: center;
`;

const Input = styled.input`
  padding: var(--space-m) var(--space-l);
  border-radius: 10px;
  border: 1px solid var(--color-light-2);
  font-size: var(--font-size-default);
`;

const Button = styled.button`
  border: 0;
  border-radius: 10px;
  padding: var(--space-m) var(--space-2xl);
  font-weight: 700;
  cursor: pointer;
  color: var(--color-light);
  background: var(--color-secondary);
`;

export default function StudentPractice() {
  const [courseNumber, setCourseNumber] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  function open() {
    if (!courseNumber.trim()) return;
    setIsOpen(true);
  }

  function close() {
    setIsOpen(false);
  }

  return (
    <>
      <StyledStudentPractice>
        <Title>Student dashboard</Title>

        <CourseContainer>
          <Input
            value={courseNumber}
            onChange={(e) => setCourseNumber(e.target.value)}
            placeholder="Enter course number"
          />
          <Button type="button" onClick={open}>
            Start AI practice
          </Button>
        </CourseContainer>
      </StyledStudentPractice>

      <StudentPracticeModal
        isOpen={isOpen}
        onClose={close}
        courseNumber={courseNumber}
      />
    </>
  );
}
