const COURSE_ID = "demo-course-220";
const ASSESSMENT_ID = "demo-assessment-oral-1";
const RUBRIC_ID = "demo-rubric-oral-1";
const MATERIAL_ID = "demo-material-notes";

const studentNames = [
  "Alex Morgan", "Jamie Chen", "Taylor Singh", "Jordan Lee",
  "Casey Brooks", "Morgan Rivera", "Riley Patel", "Avery Kim",
  "Quinn Davis", "Devon Walker", "Samira Noor", "Cameron Blake",
  "Drew Foster", "Hayden Park", "Finley Ross", "Sydney Hart",
  "Reese Nguyen", "Parker Ellis", "Rowan Cole", "Emery Shah",
  "Logan Price", "Blair Evans", "Sage Turner", "Micah Stone",
];

const publishedGrades = [88, 82, 91, 79, 86, 84, 76, 93, 81, 87, 90, 78, 85];
const aiGrades = [89, 84, 92, 81, 85, 83, 77, 94, 80, 88, 91, 79, 86, 82, 87, 90, 75, 84, 88];

const course = {
  id: COURSE_ID,
  course_code: "COMPSCI 220",
  course_name: "Algorithms & Data Structures",
  term: "2026S2",
  description: "Design, analysis, and implementation of fundamental algorithms and data structures.",
};

const assessment = {
  id: ASSESSMENT_ID,
  assessment_config_id: ASSESSMENT_ID,
  course_id: COURSE_ID,
  title: "Oral Assessment 1",
  description: "Explain algorithmic choices, analyse complexity, and defend trade-offs in a short oral examination.",
  status: "published",
  total_time_minute: 20,
  buffer_time_minute: 5,
  main_question_num: 3,
  follow_up_num: 1,
  release_time: "2026-09-01T09:00:00.000Z",
  due_time: "2026-10-02T23:59:00.000Z",
  rubric_id: RUBRIC_ID,
};

const draftAssessment = {
  ...assessment,
  id: "demo-assessment-oral-2",
  assessment_config_id: "demo-assessment-oral-2",
  title: "Oral Assessment 2 — Graph Algorithms",
  description: "A draft assessment covering traversal, shortest paths, and spanning trees.",
  status: "draft",
  main_question_num: 2,
  total_time_minute: 15,
  due_time: null,
};

const rubric = {
  id: RUBRIC_ID,
  total_points: 100,
  criteria_data: [
    { title: "Conceptual accuracy", description: "Explains the relevant algorithm or data structure accurately and precisely.", max_points: 35 },
    { title: "Complexity analysis", description: "Justifies time and space complexity using appropriate notation.", max_points: 25 },
    { title: "Reasoning and trade-offs", description: "Evaluates alternatives and defends design choices with clear reasoning.", max_points: 25 },
    { title: "Communication", description: "Presents a structured, coherent response using accurate technical language.", max_points: 15 },
  ],
};

const questions = [
  {
    id: "demo-question-1", question_pool_id: "demo-question-pool-1", question_index: 1,
    question_text: "Compare merge sort and quicksort for a large collection of records. Explain the factors that influence their practical performance, including worst-case behaviour and memory usage.",
    generation_provenance: { model: "demo-ai", source: "course-material" },
  },
  {
    id: "demo-question-2", question_pool_id: "demo-question-pool-1", question_index: 2,
    question_text: "A priority queue is used to schedule tasks with changing priorities. Which data structure would you choose, what operations must it support, and what are their asymptotic costs? Defend your choice.",
    generation_provenance: { model: "demo-ai", source: "course-material" },
  },
  {
    id: "demo-question-3", question_pool_id: "demo-question-pool-1", question_index: 3,
    question_text: "Describe how a hash table resolves collisions and explain how the load factor affects expected lookup performance. Include one situation where a balanced search tree would be preferable.",
    generation_provenance: { model: "demo-ai", source: "course-material" },
  },
  {
    id: "demo-question-4", question_pool_id: "demo-question-pool-1", question_index: 4,
    question_text: "Given an undirected weighted graph, outline an approach for finding a minimum spanning tree and explain why the algorithm is correct.",
    generation_provenance: { model: "demo-ai", source: "course-material" },
  },
];

const materials = [
  { id: MATERIAL_ID, filename: "COMPSCI220-lecture-notes-week-04.pdf", processing_status: "ready", is_processing_stale: false },
  { id: "demo-material-reading", filename: "algorithm-design-reading.pdf", processing_status: "ready", is_processing_stale: false },
];

const demoStudents = studentNames.map((full_name, index) => {
  const status = index < 13 ? "published" : index < 19 ? "review" : "inprogress";
  const session_id = `demo-session-${index + 1}`;
  return {
    session_id,
    student_id: `demo-student-${index + 1}`,
    student_name: full_name,
    student_email: `${full_name.toLowerCase().replaceAll(" ", ".")}@demo.example`,
    student_image: "/WhereRU.png",
    ai_suggested_score: index < 19 ? aiGrades[index] : null,
    final_grade: status === "published" ? publishedGrades[index] : null,
    status,
  };
});

const dashboard = [{
  course_code: course.course_code,
  course_name: course.course_name,
  assessment_config_id: ASSESSMENT_ID,
  assessment_title: assessment.title,
  published_average_score: 84.2,
  ai_average_score: 85.8,
  submitted_count: 19,
  total_students: 24,
  students: demoStudents,
}];

const feedback = {
  final_grade: 84,
  comments: "A thoughtful response with a clear comparison of the two algorithms. Strengthen the discussion of pivot selection and connect the complexity analysis more explicitly to the proposed use case.",
  status: "pending",
};

const aiSummary = {
  suggested_grade: 86,
  detailed_feedback: {
    "Conceptual accuracy": { suggested_points: "31 / 35", feedback: "Correctly distinguishes divide-and-conquer structure and explains the role of partitioning." },
    "Complexity analysis": { suggested_points: "21 / 25", feedback: "Identifies the average and worst-case bounds; the memory comparison could be more explicit." },
    "Reasoning and trade-offs": { suggested_points: "21 / 25", feedback: "Provides a defensible recommendation and recognises that input distribution affects the choice." },
    Communication: { suggested_points: "13 / 15", feedback: "Well structured and technically clear, with only minor hesitation when discussing pivot selection." },
  },
};

function makeTranscript(student = demoStudents[1]) {
  return {
    student: { id: student.student_id, full_name: student.student_name, email: student.student_email, image: "/WhereRU.png" },
    assessment: { title: assessment.title },
    resume_count: 0,
    blur_count: 0,
    disconnect_count: 1,
    ai_summary: aiSummary,
    session_feedback: feedback,
    transcript: [
      { message_type: "main_question", sequence_no: 1, content: "Compare merge sort and quicksort for a large collection of records. Explain the factors that influence their practical performance, including worst-case behaviour and memory usage." },
      { message_type: "student_answer", sequence_no: 2, content: "Both algorithms use divide and conquer. Merge sort gives a predictable O(n log n) running time and is stable, but it normally needs O(n) auxiliary memory. Quicksort is usually in-place and has good cache behaviour, so it is often faster in practice, although a poor pivot can lead to O(n squared) time. I would use a randomized or median-of-three pivot when the input may already be ordered." },
      { message_type: "followup_question", sequence_no: 3, content: "How would your recommendation change if the records must retain their original relative order when keys are equal?" },
      { message_type: "student_answer", sequence_no: 4, content: "I would prefer a stable merge-sort variant because preserving the relative order is then guaranteed. If memory is constrained, I would investigate an in-place stable implementation, but I would make that trade-off explicit because it is more complex." },
    ],
  };
}

const sessions = new Map(demoStudents.map((student) => [student.session_id, { answerCount: 0, student }]));

export const demo = {
  ids: { COURSE_ID, ASSESSMENT_ID, RUBRIC_ID, MATERIAL_ID },
  user: { id: "demo-instructor-1", upi: "demo-instructor", full_name: "Dr. Priya Nair", email: "priya.nair@demo.example", role: "instructor", image: "/WhereRU.png" },
  course,
  assessment,
  assessments: [assessment, draftAssessment],
  rubric,
  questions,
  materials,
  dashboard,
  sessions,
  makeTranscript,
  pendingReviews: [1, 2, 3, 4].map((index) => {
    const student = demoStudents[index];
    return {
      session: { id: student.session_id, user_s_id: student.student_id },
      user: { id: student.student_id, full_name: student.student_name, email: student.student_email, image: "/WhereRU.png" },
      course,
      assessment_config: assessment,
      aisummary: aiSummary,
      session_feedback: index === 1 ? feedback : { final_grade: null },
    };
  }),
};
