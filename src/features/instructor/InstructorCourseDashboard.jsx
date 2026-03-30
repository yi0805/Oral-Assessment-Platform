import { useLayoutEffect, useState } from "react";
import styled from "styled-components";

import { useGradebook } from "../../hooks/useGradebook";
import BodyText from "../../ui/BodyText";
import Button from "../../ui/Button";
import Heading from "../../ui/Heading";
import Input from "../../ui/Input";
import Selector from "../../ui/Selector";
import Table from "../../ui/Table";

const TopRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-l);
  margin-bottom: var(--space-xl);
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-l);
  margin-bottom: var(--space-xl);
`;

const StatBox = styled.div`
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-md);
  padding: var(--space-l);
  background: var(--color-primary-tint);
`;

const StatTitle = styled.p`
  margin: 0 0 var(--space-xs) 0;
  font-size: var(--font-size-s);
  color: var(--color-dark-2);
`;

const StatNumber = styled.p`
  margin: 0;
  font-weight: 700;
  color: var(--color-primary);
  font-size: var(--font-size-l);
`;

const ButtonRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-m);
  margin-top: var(--space-xl);
`;

const ScoreField = styled(Input)`
  width: 5rem;
  min-width: 0;
`;

const SummaryTd = styled.td`
  max-width: 28ch;
  font-size: var(--font-size-s);
  color: var(--color-dark-2);
  vertical-align: top;
`;

const InfoText = styled.p`
  color: var(--color-dark-2);
  margin: var(--space-l) 0;
`;

function getStats(students, getScore) {
  const submittedStudents = students.filter((student) => student.submitted);
  const scores = submittedStudents.map((student) => getScore(student));
  const aiScores = submittedStudents.map((student) => student.aiScore);

  const average =
    scores.length > 0
      ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      : null;

  const aiAverage =
    aiScores.length > 0
      ? Math.round(aiScores.reduce((a, b) => a + b, 0) / aiScores.length)
      : null;

  return {
    average,
    aiAverage,
    submittedCount: submittedStudents.length,
    totalCount: students.length,
  };
}

function getShownScore(student) {
  if (student.instructorScore != null && student.instructorScore !== "") {
    const value = Number(student.instructorScore);
    return Number.isFinite(value) ? value : student.aiScore;
  }

  return student.aiScore;
}

export default function InstructorCourseDashboard({ course }) {
  const {
    ensureGradebook,
    getAssessmentsForCourse,
    getStudents,
    setInstructorScore,
    setSelectedPublished,
    publishAll,
  } = useGradebook();

  const assessments = getAssessmentsForCourse(course.id);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState("");

  const assessmentId =
    assessments.length === 0
      ? ""
      : selectedAssessmentId &&
          assessments.some(
            (assessment) => assessment.id === selectedAssessmentId,
          )
        ? selectedAssessmentId
        : (assessments[0]?.id ?? "");

  useLayoutEffect(() => {
    if (course.id && assessmentId) {
      ensureGradebook(course.id, assessmentId);
    }
  }, [course.id, assessmentId, ensureGradebook]);

  const students = getStudents(course.id, assessmentId);
  const [draftScores, setDraftScores] = useState({});
  const [selectedStudentIds, setSelectedStudentIds] = useState(() => new Set());

  function getDraftKey(studentId) {
    return `${course.id}|${assessmentId}|${studentId}`;
  }

  function handleAssessmentChange(e) {
    setSelectedAssessmentId(e.target.value);
    setDraftScores({});
    setSelectedStudentIds(new Set());
  }

  function toggleStudent(id) {
    setSelectedStudentIds((prev) => {
      const next = new Set(prev);

      if (next.has(id)) next.delete(id);
      else next.add(id);

      return next;
    });
  }

  function handlePublishSelected() {
    if (!course.id || !assessmentId || selectedStudentIds.size === 0) return;

    setSelectedPublished(
      course.id,
      assessmentId,
      [...selectedStudentIds],
      true,
    );
    setSelectedStudentIds(new Set());
  }

  function handlePublishAll() {
    if (!course.id || !assessmentId) return;
    publishAll(course.id, assessmentId);
  }

  const stats = students ? getStats(students, getShownScore) : null;

  if (assessments.length === 0) {
    return (
      <>
        {/* <TopRow>
          <Button type="button" $variant="secondary" onClick={onBack}>
            Back to courses
          </Button>
        </TopRow> */}

        <Heading $variant="page">{course.name}</Heading>
        <BodyText>No assessments yet for this course.</BodyText>
      </>
    );
  }

  if (!students) {
    return (
      <>
        {/* <TopRow>
          <Button type="button" $variant="secondary" onClick={onBack}>
            Back to courses
          </Button>
        </TopRow> */}

        <InfoText>Loading gradebook...</InfoText>
      </>
    );
  }

  return (
    <>
      <main className="min-h-screen bg-surface pl-64 pt-24">    
        {/* <Button type="button" $variant="secondary" onClick={onBack}>
          Back to course page
        </Button> */}
        <div className="mx-auto max-w-7xl px-10 pb-20">
          <header
            className="mb-12 flex flex-col justify-between gap-6 md:flex-row md:items-end"
          >
            <div>
              <span
                className="mb-2 block text-[11px] font-bold uppercase tracking-[0.2em] text-secondary"
                >Dashboard</span
              >
              <h1
                className="font-headline text-4xl font-extrabold tracking-tight text-on-surface"
              >
                {course.name}
              </h1>
              <p
                className="mt-2 max-w-xl font-body leading-relaxed text-on-surface-variant"
              >
                Manage your academic syllabus, track curriculum progress, and
                update course materials for the upcoming semester.
              </p>
          </div>
          </header>
        </div>


      </main>

      {/* <TopRow>
        back to course page was here ##
        <div>
          <label
            htmlFor="assessment-select"
            style={{ display: "block", fontSize: "var(--font-size-s)" }}
          >
            Assessment
          </label>

          <Selector
            id="assessment-select"
            value={assessmentId}
            onChange={handleAssessmentChange}
            style={{ marginTop: "var(--space-xs)" }}
          >
            {assessments.map((assessment) => (
              <option key={assessment.id} value={assessment.id}>
                {assessment.name}
              </option>
            ))}
          </Selector>
        </div>
      </TopRow> */}

      <Heading $variant="page">{course.name}</Heading>

      {stats ? (
        <StatsGrid>
          <StatBox>
            <StatTitle>Class average</StatTitle>
            <StatNumber>
              {stats.average != null ? `${stats.average}%` : "—"}
            </StatNumber>
          </StatBox>

          <StatBox>
            <StatTitle>Submitted</StatTitle>
            <StatNumber>
              {stats.submittedCount} / {stats.totalCount}
            </StatNumber>
          </StatBox>

          <StatBox>
            <StatTitle>AI average</StatTitle>
            <StatNumber>
              {stats.aiAverage != null ? `${stats.aiAverage}%` : "—"}
            </StatNumber>
          </StatBox>
        </StatsGrid>
      ) : null}

      <Table>
        <thead>
          <tr>
            <th>Publish</th>
            <th>Student</th>
            <th>AI score</th>
            <th>AI summary</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {students.map((student) => {
            const key = getDraftKey(student.id);

            const currentValue =
              draftScores[key] !== undefined
                ? draftScores[key]
                : student.instructorScore != null
                  ? String(student.instructorScore)
                  : "";

            return (
              <tr key={student.id}>
                <td>
                  {student.submitted ? (
                    <input
                      type="checkbox"
                      checked={selectedStudentIds.has(student.id)}
                      onChange={() => toggleStudent(student.id)}
                      aria-label={`Select ${student.name}`}
                    />
                  ) : (
                    "—"
                  )}
                </td>

                <td>{student.name}</td>

                <td>{student.submitted ? `${student.aiScore}%` : "—"}</td>

                <SummaryTd>{student.aiSummary}</SummaryTd>

                <td>
                  {student.submitted ? (
                    <ScoreField
                      type="number"
                      min={0}
                      max={100}
                      step={1}
                      aria-label={`Score for ${student.name}`}
                      value={currentValue}
                      onChange={(e) =>
                        setDraftScores((prev) => ({
                          ...prev,
                          [key]: e.target.value,
                        }))
                      }
                      onBlur={() => {
                        const value = draftScores[key];
                        if (value === undefined) return;

                        setInstructorScore(
                          course.id,
                          assessmentId,
                          student.id,
                          value,
                        );
                      }}
                    />
                  ) : (
                    "—"
                  )}
                </td>

                <td>
                  {student.published
                    ? "Published"
                    : student.submitted
                      ? "Not published"
                      : "Not submitted"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </Table>

      <ButtonRow>
        <Button
          type="button"
          $variant="primary"
          onClick={handlePublishSelected}
          disabled={selectedStudentIds.size === 0}
        >
          Publish selected
        </Button>

        <Button type="button" $variant="secondary" onClick={handlePublishAll}>
          Publish all
        </Button>
      </ButtonRow>
      
    </>
  );
}
