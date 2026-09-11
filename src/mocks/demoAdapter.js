import { demo } from "./demoData";

function getPath(config) {
  const rawUrl = config.url || "";
  try {
    return new URL(rawUrl, config.baseURL || window.location.origin).pathname
      .replace(/^\/api/, "")
      .replace(/\/$/, "") || "/";
  } catch {
    return rawUrl.split("?")[0].replace(/\/$/, "") || "/";
  }
}

function response(config, data, status = 200) {
  return Promise.resolve({
    data,
    status,
    statusText: status === 200 ? "OK" : "Created",
    headers: {},
    config,
    request: null,
  });
}

function getSession(sessionId) {
  return demo.sessions.get(sessionId) || { answerCount: 0, student: demo.dashboard[0].students[0] };
}

function startSession(config, assessmentConfigId) {
  const sessionId = "demo-session-live";
  demo.sessions.set(sessionId, { answerCount: 0, student: demo.dashboard[0].students[0] });

  return response(config, {
    session_id: sessionId,
    assessment_title: demo.assessment.title,
    main_question_num: 3,
    follow_up_num: 1,
    expires_at: new Date(Date.now() + 20 * 60 * 1000).toISOString(),
    current_question: {
      question_id: "demo-question-1",
      question_text: demo.questions[0].question_text,
      main_group_no: 1,
      followup_no: 0,
      is_followup: false,
    },
    can_complete: false,
    assessment_config_id: assessmentConfigId,
  });
}

export function demoAdapter(config) {
  const path = getPath(config);
  const method = (config.method || "get").toLowerCase();
  const { COURSE_ID, ASSESSMENT_ID, RUBRIC_ID, MATERIAL_ID } = demo.ids;

  if (path === "/auth/google/me") return response(config, demo.user);
  if (path === "/auth/google/logout") return response(config, { message: "Demo session ended." });
  if (path === "/courses" && method === "get") return response(config, [demo.course]);
  if (path === "/courses/join-requests") return response(config, { pending_for_review: [], my_pending: [], my_results: [] });
  if (path === `/courses/${COURSE_ID}/instructor/dashboard`) return response(config, demo.dashboard);
  if (path === `/courses/${COURSE_ID}/assessments` && method === "get") return response(config, demo.assessments);
  if (path === `/courses/${COURSE_ID}/enrolledusers`) {
    return response(config, [
      { full_name: demo.user.full_name, upi: demo.user.upi, role: "instructor" },
      ...demo.dashboard[0].students.map((student) => ({ full_name: student.student_name, upi: student.student_email.split("@")[0], role: "student" })),
    ]);
  }
  if (path === `/courses/${COURSE_ID}/assessments/${ASSESSMENT_ID}`) return response(config, demo.assessment);
  if (path === `/courses/${COURSE_ID}/assessments/demo-assessment-oral-2`) return response(config, demo.assessments[1]);

  if (path === "/pendingReviews") return response(config, demo.pendingReviews);
  if (path === "/notifications") return response(config, []);
  if (path.startsWith("/transcript/")) {
    const session = getSession(path.split("/").pop());
    return response(config, demo.makeTranscript(session.student));
  }
  if (path === `/courses/${COURSE_ID}/my-assessment-sessions`) {
    return response(config, [{
      assessment_config_id: ASSESSMENT_ID,
      title: demo.assessment.title,
      description: demo.assessment.description,
      status: "not_started",
      due_time: demo.assessment.due_time,
      total_time_minute: demo.assessment.total_time_minute,
      main_question_num: demo.assessment.main_question_num,
      follow_up_num: demo.assessment.follow_up_num,
    }]);
  }
  if (path === `/courses/${COURSE_ID}/my-assessment-history`) {
    return response(config, {
      class_average_grade: 81.4,
      items: [{
        session_id: "demo-session-1",
        assessment_title: "Oral Assessment 0 — Foundations",
        final_grade: 86,
        submitted_at: "2026-08-18T10:30:00.000Z",
        comments: "Clear explanation of invariants and a well-chosen example.",
        instructor_name: demo.user.full_name,
        instructor_image: "/WhereRU.png",
      }],
    });
  }
  if (path.startsWith(`/assessments/${ASSESSMENT_ID}/sessions/start`)) return startSession(config, ASSESSMENT_ID);
  if (path.startsWith("/sessions/") && path.endsWith("/respond")) {
    const session = getSession(path.split("/")[2]);
    session.answerCount += 1;
    const nextQuestion = session.answerCount === 1
      ? { question_id: "demo-followup-1", question_text: "If the input is already sorted, how would you adapt your quicksort implementation to reduce the risk of worst-case behaviour?", main_group_no: 1, followup_no: 1, is_followup: true }
      : session.answerCount === 2
        ? { question_id: "demo-question-2", question_text: demo.questions[1].question_text, main_group_no: 2, followup_no: 0, is_followup: false }
        : null;
    return response(config, { next_question: nextQuestion, can_complete: !nextQuestion });
  }
  if (path.startsWith("/sessions/") && path.endsWith("/transcribe/audio")) {
    return response(config, { transcript: "Merge sort has predictable O(n log n) performance and is stable, while quicksort is often faster in practice because it can work in place. The trade-off is quicksort's O(n squared) worst case if pivots are chosen poorly." });
  }
  if (path.startsWith("/sessions/") && path.endsWith("/complete")) return response(config, { message: "Assessment completed in demo mode." });
  if (path.includes("/blur-notification") || path.includes("/reconnect-notification")) return response(config, { message: "Demo integrity event recorded." });
  if (path === "/sessions/release/allSessions" || path === "/sessions/ai-summary/approve/all") return response(config, { message: "Demo results updated." });
  if (path.startsWith("/sessions/") && (path.endsWith("/grade") || path.endsWith("/review") || path.includes("/release/session") || path.includes("/unpublish/session") || path.endsWith("/ai-summary/approve"))) return response(config, { message: "Demo review updated." });

  if (path === `/assessments/${ASSESSMENT_ID}/questions`) return response(config, demo.questions);
  if (path === `/assessments/${ASSESSMENT_ID}/rubric`) return response(config, demo.rubric);
  if (path.startsWith("/questions/") && path.endsWith("/supporting-context")) {
    return response(config, {
      source_material_ids: [MATERIAL_ID],
      source_chunk_ids: ["demo-chunk-1"],
      model: "demo-ai",
      generated_at: "2026-09-10T11:00:00.000Z",
      prompt_version: "demo-v1",
      contexts: [{ material_id: MATERIAL_ID, material_filename: "COMPSCI220-lecture-notes-week-04.pdf", chunk_id: "demo-chunk-1", chunk_index: 2, text: "Stable sorting preserves the relative order of records with equal keys. Merge sort provides this guarantee naturally, while quicksort requires a stable partitioning strategy." }],
    });
  }
  if (path === `/courses/${COURSE_ID}/generate-question` && method === "post") return response(config, { assessment_config: ASSESSMENT_ID, questions: demo.questions }, 201);
  if (path.includes("/questions") && ["post", "put", "delete"].includes(method)) return response(config, { message: "Demo question updated." });
  if (path.endsWith("/release") || (path.includes("/assessments/") && path.endsWith("/copy"))) return response(config, { message: "Demo assessment updated.", sessions_created: 24 });

  if (path.includes("/materials/upload") || path.endsWith("/materials/github")) return response(config, { id: MATERIAL_ID, processing_status: "ready" }, 201);
  if (path.includes("/materials/") && (path.endsWith("/status") || path.endsWith("/retry"))) return response(config, demo.materials[0]);
  if (path === `/courses/${COURSE_ID}/rubrics` && method === "post") return response(config, demo.rubric, 201);
  if (path.startsWith(`/assessments/${RUBRIC_ID}/rubric`) || path === `/assessments/${ASSESSMENT_ID}/rubric`) return response(config, demo.rubric);
  if (path.includes("/assessments/") && ["put", "delete"].includes(method)) return response(config, { message: "Demo assessment updated." });
  if (path.startsWith("/users/")) return response(config, demo.user);

  return response(config, { message: "Demo mode: no network request was made." });
}
