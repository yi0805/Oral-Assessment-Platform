import { useMemo, useState } from "react";
import styled from "styled-components";

import { useGradebook } from "../../hooks/useGradebook";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import SearchBar from "../../ui/SearchBar";
import Button from "../../ui/Button";
import Input from "../../ui/Input";

import InstructorCourseDashboard from "./InstructorCourseDashboard";

const TopBar = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-l);
  margin-bottom: var(--space-xl);
`;

const SearchWrap = styled.div`
  flex: 1;
  min-width: 200px;
  max-width: 420px;
  margin-left: auto;
`;

const CourseGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-xl);
`;

const CourseCard = styled.button`
  border: 1px solid var(--color-light-2);
  border-radius: 12px;
  background: var(--color-light);
  cursor: pointer;
  padding: 0;
  text-align: left;
  font: inherit;
  color: inherit;

  &:focus-visible {
    outline: 2px solid var(--color-secondary);
    outline-offset: 2px;
  }
`;

const CardPhoto = styled.div`
  height: 120px;
  background: ${({ $color }) => $color};
  border-radius: 12px 12px 0 0;
`;

const CardFooter = styled.div`
  padding: var(--space-m);
`;

const CourseName = styled.p`
  margin: 0;
  font-weight: 600;
  color: var(--color-primary);
`;

const AddCourseCard = styled.button`
  border: 2px dashed var(--color-light-2);
  border-radius: 12px;
  background: var(--color-primary-tint);
  min-height: 168px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xxl);
  font-weight: 700;
  color: var(--color-secondary);
  cursor: pointer;
  font: inherit;

  &:hover {
    border-color: var(--color-secondary);
    background: var(--color-secondary-tint);
  }

  &:focus-visible {
    outline: 2px solid var(--color-secondary);
    outline-offset: 2px;
  }
`;

const EmptyState = styled.p`
  margin-top: var(--space-l);
  color: var(--color-dark-2);
`;

const FormStack = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-m);
  margin-top: var(--space-l);
  max-width: 40ch;
`;

const FormActions = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-m);
  margin-top: var(--space-m);
`;

const AddPanel = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-md);
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
  background: var(--color-primary-tint);
`;

const FieldLabel = styled.label`
  display: block;
  font-size: var(--font-size-s);
  color: var(--color-dark-2);
  margin-bottom: var(--space-xs);
`;

function InstructorHome() {
  const { allCourses, addCourse } = useGradebook();
  const [search, setSearch] = useState("");
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [courseCode, setCourseCode] = useState("");
  const [courseName, setCourseName] = useState("");
  const [courseDesc, setCourseDesc] = useState("");

  const shownCourses = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return allCourses;

    return allCourses.filter(
      (course) =>
        course.code.toLowerCase().includes(value) ||
        course.name.toLowerCase().includes(value) ||
        (course.description &&
          course.description.toLowerCase().includes(value)),
    );
  }, [allCourses, search]);

  function handleAddCourse(e) {
    e.preventDefault();

    if (!courseCode.trim() || !courseName.trim()) return;

    addCourse({
      code: courseCode,
      name: courseName,
      description: courseDesc,
    });

    setCourseCode("");
    setCourseName("");
    setCourseDesc("");
    setShowAddForm(false);
  }

  if (selectedCourse) {
    return (
      <ContentCard>
        <InstructorCourseDashboard
          key={selectedCourse.id}
          course={selectedCourse}
          onBack={() => setSelectedCourse(null)}
        />
      </ContentCard>
    );
  }

  return (
    <ContentCard>
      <TopBar>
        <Heading $variant="page" style={{ marginBottom: 0 }}>
          My Courses
        </Heading>

        <SearchWrap>
          <SearchBar
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by course code or name"
          />
        </SearchWrap>
      </TopBar>

      {showAddForm && (
        <AddPanel>
          <Heading
            as="h2"
            $variant="page"
            style={{
              fontSize: "var(--font-size-l)",
              marginBottom: "var(--space-m)",
            }}
          >
            Add Course
          </Heading>

          <form onSubmit={handleAddCourse}>
            <FormStack>
              <div>
                <FieldLabel htmlFor="new-course-code">Course code</FieldLabel>
                <Input
                  id="new-course-code"
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  placeholder="e.g. COMPSCI 101"
                  required
                />
              </div>

              <div>
                <FieldLabel htmlFor="new-course-name">Course name</FieldLabel>
                <Input
                  id="new-course-name"
                  value={courseName}
                  onChange={(e) => setCourseName(e.target.value)}
                  placeholder="e.g. Intro to CS"
                  required
                />
              </div>

              <div>
                <FieldLabel htmlFor="new-course-desc">
                  Description (optional)
                </FieldLabel>
                <Input
                  id="new-course-desc"
                  value={courseDesc}
                  onChange={(e) => setCourseDesc(e.target.value)}
                  placeholder="Short course description"
                />
              </div>
            </FormStack>

            <FormActions>
              <Button type="submit" $variant="primary">
                Add course
              </Button>
              <Button
                type="button"
                $variant="secondary"
                onClick={() => setShowAddForm(false)}
              >
                Cancel
              </Button>
            </FormActions>
          </form>
        </AddPanel>
      )}

      {shownCourses.length === 0 && <EmptyState>No courses found.</EmptyState>}

      <CourseGrid>
        {shownCourses.map((course) => (
          <CourseCard
            key={course.id}
            type="button"
            onClick={() => setSelectedCourse(course)}
          >
            <CardPhoto $color={course.color} />
            <CardFooter>
              <CourseName>{course.name}</CourseName>
            </CardFooter>
          </CourseCard>
        ))}

        <AddCourseCard
          type="button"
          onClick={() => setShowAddForm(true)}
          aria-label="Add course"
        >
          +
        </AddCourseCard>
      </CourseGrid>
    </ContentCard>
  );
}

export default InstructorHome;
