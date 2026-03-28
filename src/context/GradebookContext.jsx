import { useCallback, useEffect, useMemo, useState } from "react";

import mockAssessments from "../data/mockAssessments";
import mockCourses from "../data/mockCourses";

import {
  loadGradebookState,
  saveGradebookState,
} from "../utils/gradebookStorage";

import { createContext } from "react";

const GradebookContext = createContext();

const COURSE_IMAGE = [  
  "https://lh3.googleusercontent.com/aida-public/AB6AXuDfgr_pP5i7hQoboiS_DsxFRPWBpPHlHpUXumClpddDt2JX7BsTy1RucSS9hAnXPHskftAHFN-qV7kXv61MwoKaNkxvqx41RxJsHnItt2OmhV9TcIGhNkjwwWJDIJBpGx1OVaevsdmzLdL53qdnBksk7Ks2vMWDlbrBRf0JdHg25PrboJ2OYXhx8vTxAta6zZTLt7dT2JXlzV-OxVl6RPR0-L5aXHJxzBKh-c8MTw86BqkmHDoPdgqjbfQS5aA-OmT8pNhuXzlc9KnW",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuB_TjDjVsjnTlwmwB0gDWQ-U-AahXp_b8lpZ14Py7eMk63zOzkUqUQY-fl84SbQNLlfXPTSiOIRYU2xEJifhcY4N89ZTCr_TgabEFJOIB3cWQ6Z3jbHwc1PgxOq1jlbQ8iDTpIqVZygzlUnDqyjLMls7D0mxC5SVAM72ouBfbQxbsry7nnfEvvz4N_98td94vnn2IeNKd1h7VtcH-K_2IxLA3Oyj9lJSAjpyhlIt1Q2PNLzsuWcShb3aU5ul55WCaN6KbiRdFrrKkwr",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuBkdEcmqThK9dB3ArCqjwxvzz0_opItvI_4i5g5B7fE9L9qJWK4DObWAy-H_so9vgD-23qb2yHLjtLT9BFh8XFyu04NVBfRxEjOqvlsjG3M9Tp-oMfFMp3zlWeSnECBfU5vCdos9eKFWh-_NoPZekYd2X7W54Bx7_PW4XYDBzoIZO3qPpmkeTUlMHXH2wQV1sjNGM9M4JUfQFKSxVpQ4edkqmDEPnWfGhBSdPhq-DcrNyUu3HFuMvugK6n5-f_mGHhyk5M-V3F7jXAS",
  "https://lh3.googleusercontent.com/aida-public/AB6AXuD3shRtSi9buB-3A-lLTQ-XDY7NQG2J-VCj0tz2hARiNzaRoOFQrXO9Wl68MzBMooDvHYVyHO_AFPzg-dzGNVkNiWxfHaCW5dK13_iHPu2I1ShEejxdAYAe4Jnmr4FWg-mgmZKoifN0QGfj5cBQNLdYT2deMzRZY2xM_a-Y8SbUmZHORRYEYRhk9R6f0TbxWHcn4IZ0YmXGfhHXADRdSOMKeCtdWd57cobtYtdTZKLkprfY_hZlHhTroGscGQlV6tj67fIz5x3pPsoA",
    
];

function createStudent(id, name, aiScore, aiSummary, submitted = true) {
  return {
    id,
    name,
    aiScore,
    aiSummary,
    instructorScore: null,
    submitted,
    published: false,
  };
}

function getDefaultStudents() {
  return [
    createStudent(
      "s1",
      "Alice",
      82,
      "Pretty clear overall. The last question needed a bit more detail.",
    ),
    createStudent(
      "s2",
      "Ben",
      71,
      "Decent attempt, but some of the basic ideas were a bit shaky.",
    ),
    createStudent(
      "s3",
      "Chen",
      91,
      "Really strong submission. Answers were clear and confident.",
    ),
    createStudent(
      "s4",
      "Dana",
      0,
      "Nothing submitted for this assessment.",
      false,
    ),
  ];
}

function getInitialState() {
  return {
    gradebook: {},
    extraCourses: [],
    customAssessments: {},
  };
}

function copyState(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function getCourseAssessments(courseId, customAssessments) {
  const defaultAssessments = mockAssessments[courseId] || [];
  const addedAssessments = customAssessments[courseId] || [];
  return [...defaultAssessments, ...addedAssessments];
}

function getFinalScore(student) {
  if (student.instructorScore != null && student.instructorScore !== "") {
    const score = Number(student.instructorScore);
    return Number.isFinite(score) && score <= 100 ? score : student.aiScore;
  }

  return student.aiScore;
}

function isSameStudent(rosterName, userName) {
  const roster = rosterName.trim().toLowerCase();
  const user = userName.trim().toLowerCase();

  if (!roster || !user) return false;
  if (roster === user) return true;

  const rosterFirstName = roster.split(/\s+/)[0];
  const userFirstName = user.split(/\s+/)[0];

  return rosterFirstName === userFirstName;
}

function GradebookProvider({ children }) {
  const [state, setState] = useState(() => {
    const savedState = loadGradebookState();
    return savedState && typeof savedState === "object"
      ? savedState
      : getInitialState();
  });

  useEffect(() => {
    saveGradebookState(state);
  }, [state]);

  const allCourses = useMemo(() => {
    return [...mockCourses, ...state.extraCourses];
  }, [state.extraCourses]);

  const ensureGradebook = useCallback((courseId, assessmentId) => {
    setState((prev) => {
      const next = copyState(prev);

      if (!next.gradebook[courseId]) {
        next.gradebook[courseId] = {};
      }

      if (!next.gradebook[courseId][assessmentId]) {
        next.gradebook[courseId][assessmentId] = {
          students: getDefaultStudents(),
        };
      }

      return next;
    });
  }, []);

  const getAssessmentsForCourse = useCallback(
    (courseId) => {
      return getCourseAssessments(courseId, state.customAssessments);
    },
    [state.customAssessments],
  );

  const getStudents = useCallback(
    (courseId, assessmentId) => {
      return state.gradebook[courseId]?.[assessmentId]?.students ?? null;
    },
    [state.gradebook],
  );

  const setInstructorScore = useCallback(
    (courseId, assessmentId, studentId, value) => {
      setState((prev) => {
        const next = copyState(prev);

        if (!next.gradebook[courseId]?.[assessmentId]) return prev;

        const student = next.gradebook[courseId][assessmentId].students.find(
          (row) => row.id === studentId,
        );

        if (!student) return prev;

        const score = value === "" ? null : Number(value);
        student.instructorScore = Number.isFinite(score) ? score : null;

        return next;
      });
    },
    [],
  );

  const setSelectedPublished = useCallback(
    (courseId, assessmentId, studentIds, published) => {
      setState((prev) => {
        const next = copyState(prev);
        const students = next.gradebook[courseId]?.[assessmentId]?.students;

        if (!students) return prev;

        for (const student of students) {
          if (studentIds.includes(student.id)) {
            student.published = published;
          }
        }

        return next;
      });
    },
    [],
  );

  const publishAll = useCallback((courseId, assessmentId) => {
    setState((prev) => {
      const next = copyState(prev);
      const students = next.gradebook[courseId]?.[assessmentId]?.students;

      if (!students) return prev;

      for (const student of students) {
        if (student.submitted) {
          student.published = true;
        }
      }

      return next;
    });
  }, []);

  const addCourse = useCallback(({ code, name, description }) => {
    const id = `Yi-${Date.now()}`;
    const image =
      COURSE_IMAGE[
        (mockCourses.length + Math.floor(Math.random() * 10)) %
          COURSE_IMAGE.length
      ];

    const newCourse = {
      id,
      code: code.trim(),
      name: name.trim(),
      description: (description || "").trim(),
      image,
    };

    setState((prev) => ({
      ...prev,
      extraCourses: [...prev.extraCourses, newCourse],
    }));

    return newCourse;
  }, []);

  const addCustomAssessment = useCallback(
    ({ courseId, name, difficulty, pdfFileName }) => {
      const id = `Yi-${Date.now()}`;

      const newAssessment = {
        id,
        name: name.trim(),
        deadline: "TBA",
        teacherNote: `Created from ${pdfFileName || "the uploaded PDF"} with ${difficulty} difficulty.`,
        difficulty,
        pdfFileName: pdfFileName || "",
        generatedQuestions: [
          "What is the main point of this document in your own words?",
          "What are three key ideas you noticed from the reading?",
          "Can you give one practical example of how you would use an idea from this document?",
        ],
      };

      setState((prev) => {
        const next = copyState(prev);

        if (!next.customAssessments[courseId]) {
          next.customAssessments[courseId] = [];
        }

        next.customAssessments[courseId].push(newAssessment);

        if (!next.gradebook[courseId]) {
          next.gradebook[courseId] = {};
        }

        next.gradebook[courseId][id] = {
          students: getDefaultStudents(),
        };

        return next;
      });

      return newAssessment;
    },
    [],
  );

  const getPublishedScoreForStudent = useCallback(
    (courseId, assessmentId, userName) => {
      if (!userName) return null;

      const students =
        state.gradebook[courseId]?.[assessmentId]?.students ?? [];

      const student = students.find(
        (row) =>
          row.published && row.submitted && isSameStudent(row.name, userName),
      );

      if (!student) return null;

      return getFinalScore(student);
    },
    [state.gradebook],
  );

  const value = useMemo(
    () => ({
      state,
      allCourses,
      ensureGradebook,
      getAssessmentsForCourse,
      getStudents,
      setInstructorScore,
      setSelectedPublished,
      publishAll,
      addCourse,
      addCustomAssessment,
      getPublishedScoreForStudent,
    }),
    [
      state,
      allCourses,
      ensureGradebook,
      getAssessmentsForCourse,
      getStudents,
      setInstructorScore,
      setSelectedPublished,
      publishAll,
      addCourse,
      addCustomAssessment,
      getPublishedScoreForStudent,
    ],
  );

  return (
    <GradebookContext.Provider value={value}>
      {children}
    </GradebookContext.Provider>
  );
}

export { GradebookProvider, GradebookContext };
