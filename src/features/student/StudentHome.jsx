import { useState } from "react";
import { useNavigate } from "react-router";
import styled from "styled-components";

import mockCourses from "../../data/mockCourses";
import Heading from "../../ui/Heading";
import SearchBar from "../../ui/SearchBar";

const SearchWrapper = styled.div`
  margin-bottom: var(--space-xl);
  right: 0;
  float: right;
  width: 460px;
`;

const Head = styled.div`
  flex: 1;
  flex-direction: row;
  overflow: hidden;  
`;

const Container = styled.div`
  height: auto;
  border-radius: var(--radius-md);
  max-width: 100%;
  background: white;
  padding: var(--space-3xl);
  margin: 0 0 10px 0;
`;

const CourseGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(365px, 1fr));
  gap: var(--space-xl);
`;

const CourseCard = styled.div`
  border-radius: var(--radius-md);
  background: radial-gradient(ellipse at left top, #d2faf6, ${({ $color }) => $color} 45%);
  cursor: pointer;
  height: 16rem;
  width: 24rem;
  position: relative;
  box-shadow: 5px 8px 8px 0 #1e1e2132;
`;

const CardBody = styled.div`
  padding: var(--space-m);
  position: absolute;
  bottom: 0;
  background: white;
  width: 100%;
  min-height: 170px;
  border-radius: 0 0 12px 12px;
`;

const CourseCode = styled.p`
  font-size: var(--font-size-s);
  font-weight: 600;
  margin: 0 0 0.3rem 0;
  color: var(--color-secondary);
`;

const CourseName = styled.h3`
  margin: 0;
  font-weight: 600;
  color: var(--color-dark);
`;

const CourseDesc = styled.p`
  margin: 0 0 0.3rem 0;
  colour: var(--color-dark-3-tint);
`;

const EmptyState = styled.p`
  margin-top: var(--space-l);
  color: var(--color-dark-2);
`;

export default function StudentHome() {
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filtered = mockCourses.filter(
    (course) =>
      course.code.toLowerCase().includes(search.toLowerCase()) ||
      course.name.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <>
      <Container>
        <Head>
          <Heading $variant="page">My Courses</Heading>
          <SearchWrapper>
            <SearchBar
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search courses..."
            />
          </SearchWrapper>
        </Head>
        <CourseDesc>Welcome and play with our website!</CourseDesc>
      </Container>

      {filtered.length === 0 ? (
        <EmptyState>No courses match your search.</EmptyState>
      ) : (
        <Container>
          <CourseGrid>
            {filtered.map((course) => (
              <CourseCard
                key={course.id}
                $color={course.color}
                onClick={() => navigate(`/courses/${course.id}/assignments`)}
              >
                {/* <CardBanner $color={course.color} /> */}
                <CardBody>
                  <CourseCode>{course.code}</CourseCode>
                  <CourseName>{course.name}</CourseName>
                  <CourseDesc>a short description of anything ^^</CourseDesc>
                </CardBody>
              </CourseCard>
            ))}
          </CourseGrid>
        </Container>
      )}
    </>
  );
}
