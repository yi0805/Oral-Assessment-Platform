import { useState } from "react";
import { useParams, useNavigate } from "react-router";
import styled from "styled-components";

import mockCourses from "../../data/mockCourses";
import mockAssessments from "../../data/mockAssessments";
import Heading from "../../ui/Heading";
import SearchBar from "../../ui/SearchBar";
import ButtonLink from "../../ui/ButtonLink";

const BackButton = styled(ButtonLink)`
  margin-bottom: var(--space-l);
`;

const SearchWrapper = styled.div`
  margin-bottom: var(--space-xl);
`;

const AssessmentList = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
`;

const AssessmentCard = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: 12px;
  background: var(--color-light);
  padding: var(--space-l);
  cursor: pointer;
`;

const AssessmentName = styled.h3`
  margin: 0 0 0.4rem 0;
  color: var(--color-primary);
  font-size: var(--font-size-default);
`;

const Deadline = styled.p`
  margin: 0 0 0.3rem 0;
  color: var(--color-dark-2);
  font-size: var(--font-size-s);
`;

const TeacherNote = styled.p`
  margin: 0;
  color: var(--color-dark-2);
  font-size: var(--font-size-s);
`;

const EmptyState = styled.p`
  margin-top: var(--space-l);
  color: var(--color-dark-2);
`;

export default function StudentAssignments() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  const course = mockCourses.find((c) => c.id === courseId);
  const assessments = mockAssessments[courseId] || [];

  const filtered = assessments.filter((assessment) =>
    assessment.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <BackButton to="/home" $variant="secondary">
        Back to Courses
      </BackButton>

      <Heading $variant="page">
        {course ? `${course.code} - ${course.name}` : "Assignments"}
      </Heading>

      <SearchWrapper>
        <SearchBar
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search assessments..."
        />
      </SearchWrapper>

      {filtered.length === 0 ? (
        <EmptyState>No assessments match your search.</EmptyState>
      ) : (
        <AssessmentList>
          {filtered.map((assessment) => (
            <AssessmentCard
              key={assessment.id}
              onClick={() =>
                navigate(`/courses/${courseId}/assessments/${assessment.id}`)
              }
            >
              <AssessmentName>{assessment.name}</AssessmentName>
              <Deadline>Due: {assessment.deadline}</Deadline>
              <TeacherNote>{assessment.teacherNote}</TeacherNote>
            </AssessmentCard>
          ))}
        </AssessmentList>
      )}
    </>
  );
}
