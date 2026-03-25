import { useState } from "react";
import { useNavigate } from "react-router";
import styled from "styled-components";

import { useGradebook } from "../../hooks/useGradebook";
import Heading from "../../ui/Heading";
import SearchBar from "../../ui/SearchBar";

const SearchWrapper = styled.div`
  margin-bottom: var(--space-xl);
`;

const CourseGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-xl);
`;

const CourseCard = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: 12px;
  background: var(--color-light);
  cursor: pointer;
`;

const CardBanner = styled.div`
  height: 100px;
  background: ${({ $color }) => $color};
`;

const CardBody = styled.div`
  padding: var(--space-m);
`;

const CourseCode = styled.p`
  margin: 0 0 0.3rem 0;
  font-weight: 600;
  color: var(--color-primary);
`;

const CourseName = styled.p`
  margin: 0;
  color: var(--color-dark-2);
`;

const EmptyState = styled.p`
  margin-top: var(--space-l);
  color: var(--color-dark-2);
`;

export default function StudentHome() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();
  const { allCourses } = useGradebook();

  const filtered = allCourses.filter(
    (course) =>
      course.code.toLowerCase().includes(search.toLowerCase()) ||
      course.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <Heading $variant="page">My Courses</Heading>

      <SearchWrapper>
        <SearchBar
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search courses..."
        />
      </SearchWrapper>

      {filtered.length === 0 ? (
        <EmptyState>No courses match your search.</EmptyState>
      ) : (
        <CourseGrid>
          {filtered.map((course) => (
            <CourseCard
              key={course.id}
              onClick={() => navigate(`/courses/${course.id}/assignments`)}
            >
              <CardBanner $color={course.color} />
              <CardBody>
                <CourseCode>{course.code}</CourseCode>
                <CourseName>{course.name}</CourseName>
              </CardBody>
            </CourseCard>
          ))}
        </CourseGrid>
      )}
    </>
  );
}
