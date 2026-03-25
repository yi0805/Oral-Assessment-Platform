import { useRef, useState } from "react";
import { Navigate } from "react-router";
import styled from "styled-components";

import { useGradebook } from "../hooks/useGradebook";
import useRequireAuth from "../hooks/useRequireAuth";
import Button from "../ui/Button";
import ContentCard from "../ui/ContentCard";
import Heading from "../ui/Heading";
import Input from "../ui/Input";
import Selector from "../ui/Selector";

const FormStack = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-l);
  max-width: 50ch;
  margin-top: var(--space-xl);
`;

const FieldLabel = styled.label`
  display: block;
  font-size: var(--font-size-s);
  color: var(--color-dark-2);
  margin-bottom: var(--space-xs);
`;

const FileRow = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
`;

const FileInput = styled.input`
  font-size: var(--font-size-s);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-xs);
  border: 1px solid var(--color-border);
`;

const QuestionsPanel = styled.div`
  display: flex;
  flex-direction: column;
  margin-top: var(--space-3xl);
  padding: var(--space-xl);
  border: 1px solid var(--color-light-2);
  border-radius: var(--radius-md);
  background: var(--color-primary-tint);
`;

const QuestionList = styled.ol`
  margin: var(--space-m) 0 0 var(--space-xl);
  color: var(--color-dark-2);
  line-height: 1.5;
`;

function InstructorUpdateAssessment() {
  const role = useRequireAuth();
  const { allCourses, addCustomAssessment } = useGradebook();

  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [name, setName] = useState("");
  const [level, setLevel] = useState("intermediate");
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState(null);
  const fileRef = useRef(null);

  const courseId =
    allCourses.length === 0
      ? ""
      : selectedCourseId &&
          allCourses.some((course) => course.id === selectedCourseId)
        ? selectedCourseId
        : (allCourses[0]?.id ?? "");

  if (role !== "instructor") {
    return <Navigate to="/home" replace />;
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    setFileName(file ? file.name : "");
    setQuestions(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!courseId || !name.trim() || !fileName) return;

    setLoading(true);
    setQuestions(null);

    await new Promise((resolve) => setTimeout(resolve, 1400));

    const newAssessment = addCustomAssessment({
      courseId,
      name,
      difficulty: level,
      pdfFileName: fileName,
    });

    setQuestions(newAssessment.generatedQuestions);
    setLoading(false);
    setName("");
    setFileName("");

    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <ContentCard style={{ display: "flex", flexDirection: "column" }}>
      <Heading $variant="page">Update Assessment</Heading>

      <form onSubmit={handleSubmit}>
        <FormStack>
          <div>
            <FieldLabel htmlFor="course-select">Course</FieldLabel>
            <Selector
              id="course-select"
              value={courseId}
              onChange={(e) => setSelectedCourseId(e.target.value)}
            >
              {allCourses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.code} — {course.name}
                </option>
              ))}
            </Selector>
          </div>

          <div>
            <FieldLabel htmlFor="assessment-name">Assessment name</FieldLabel>
            <Input
              id="assessment-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Midterm review"
              required
            />
          </div>

          <div>
            <FieldLabel htmlFor="difficulty">Difficulty</FieldLabel>
            <Selector
              id="difficulty"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
            >
              <option value="introductory">Introductory</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </Selector>
          </div>

          <FileRow>
            <FieldLabel htmlFor="assessment-pdf">Assessment PDF</FieldLabel>
            <FileInput
              id="assessment-pdf"
              ref={fileRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              required
            />
          </FileRow>

          <Button type="submit" $variant="primary" disabled={loading}>
            {loading ? "Generating..." : "Upload and generate questions"}
          </Button>
        </FormStack>
      </form>

      {questions?.length ? (
        <QuestionsPanel>
          <Heading
            as="h2"
            $variant="page"
            style={{
              fontSize: "var(--font-size-l)",
              marginBottom: "var(--space-m)",
            }}
          >
            Generated questions
          </Heading>

          <QuestionList>
            {questions.map((question, index) => (
              <li key={index}>{question}</li>
            ))}
          </QuestionList>
        </QuestionsPanel>
      ) : null}
    </ContentCard>
  );
}

export default InstructorUpdateAssessment;
