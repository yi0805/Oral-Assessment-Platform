// E2E happy-path test for the streaming-transcription UI added in
// issue #72. Drives the student assessment page through one record →
// partial → final → textarea cycle and asserts the documented SLA:
//
//   * partial preview appears within 1500 ms of clicking the mic
//   * final transcript lands in the textarea within 3000 ms of
//     clicking stop
//
// Backend isn't started for this test — every HTTP call is stubbed
// via page.route() and the WebSocket endpoint is intercepted with
// page.routeWebSocket() so a Playwright run is self-contained.
// getUserMedia + AudioContext are also stubbed inside the page so
// headless Chromium doesn't try to open real hardware.
//
// To run locally:
//   npm install
//   npm run test:e2e:install    # one-time, fetches chromium
//   npm run test:e2e

import { test, expect } from "@playwright/test";

const FAKE_COURSE_ID = "00000000-0000-0000-0000-0000000000c1";
const FAKE_ASSESSMENT_ID = "00000000-0000-0000-0000-0000000000a1";
const FAKE_SESSION_ID = "00000000-0000-0000-0000-0000000000c0";
const FAKE_QUESTION_ID = "00000000-0000-0000-0000-0000000000d1";

const STUDENT_URL = `/student/${FAKE_COURSE_ID}/${FAKE_ASSESSMENT_ID}`;

// Fixture transcripts: AWS first sends a partial (revised once),
// then a single final. The spec asserts both are surfaced correctly.
const FIXTURE_PARTIAL = "testing one two";
const FIXTURE_FINAL = "testing one two three four five";

test.describe("streaming transcription — happy path", () => {
  test.beforeEach(async ({ page, context }) => {
    // ---- 1. Auth cookie. The backend isn't running so the cookie
    // value is opaque — it just needs to exist for the WS handshake
    // to send something. The HTTP mocks below short-circuit auth.
    await context.addCookies([
      {
        name: "access_token",
        value: "fake-jwt-for-e2e",
        url: "http://localhost:5173",
      },
    ]);

    // ---- 2. Fake mic + AudioContext / AudioWorklet. Installed
    // before any page script runs so the streaming hook sees the
    // stubs when it imports useAudioContext.
    await page.addInitScript(() => {
      // Minimal MediaStream / track. The streaming pipeline calls
      // stream.getTracks() to release the mic on stop.
      const fakeTrack = { stop() {}, kind: "audio", enabled: true };
      const fakeStream = { getTracks: () => [fakeTrack] };

      if (
        typeof navigator !== "undefined" &&
        navigator.mediaDevices
      ) {
        navigator.mediaDevices.getUserMedia = async () => fakeStream;
      }

      class FakeAudioWorklet {
        async addModule() {
          return undefined;
        }
      }
      class FakeAudioWorkletNode {
        constructor() {
          this.port = {
            onmessage: null,
            postMessage() {},
          };
        }
        connect() {}
        disconnect() {}
      }
      class FakeMediaStreamSource {
        connect() {}
        disconnect() {}
      }
      class FakeAudioContext {
        constructor() {
          this.state = "running";
          this.destination = {};
          this.audioWorklet = new FakeAudioWorklet();
        }
        async resume() {
          this.state = "running";
        }
        async close() {
          this.state = "closed";
        }
        createMediaStreamSource() {
          return new FakeMediaStreamSource();
        }
      }
      window.AudioContext = FakeAudioContext;
      window.webkitAudioContext = FakeAudioContext;
      window.AudioWorkletNode = FakeAudioWorkletNode;
    });

    // ---- 3. Stub the backend HTTP surface that StudentAssessment
    // hits during init. We intercept everything under /api/** and
    // dispatch by URL — anything we haven't explicitly handled gets a
    // 200 with an empty JSON body so a missed endpoint doesn't blow
    // up the test for an unrelated reason.
    await page.route("**/api/**", async (route) => {
      const url = route.request().url();

      if (url.endsWith("/auth/google/me")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "00000000-0000-0000-0000-0000000000b1",
            email: "e2e-student@example.com",
            role: "student",
            name: "E2E Student",
          }),
        });
      }

      if (url.endsWith("/courses")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: FAKE_COURSE_ID,
              name: "E2E Course",
              code: "E2E101",
            },
          ]),
        });
      }

      if (url.endsWith(`/assessments/${FAKE_ASSESSMENT_ID}/sessions/start`)) {
        // Pad expires_at out far enough that the auto-complete
        // effect doesn't fire mid-test.
        const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString();
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            session_id: FAKE_SESSION_ID,
            assessment_title: "E2E Streaming Test",
            expires_at: expiresAt,
            current_question: {
              id: FAKE_QUESTION_ID,
              content: "Describe how streaming transcription works.",
              question_kind: "main",
              main_group_no: 1,
              followup_no: 0,
            },
            can_complete: false,
            main_question_num: 1,
            follow_up_num: 0,
          }),
        });
      }

      // Default — empty success so missed endpoints don't crash.
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: "{}",
      });
    });
  });

  test("partial within 1500 ms, final lands in textarea within 3000 ms", async ({
    page,
  }) => {
    // ---- 4. Intercept the streaming WebSocket. routeWebSocket gives
    // us a handle we can send canned JSON frames through; the page
    // never reaches a real server.
    await page.routeWebSocket(/\/transcribe\/stream/, (ws) => {
      // Schedule a partial ~250 ms after the page opens the socket
      // — well within the 1500 ms SLA — and a final ~250 ms after
      // the page sends its {"type":"stop"} text frame.
      const partialTimer = setTimeout(() => {
        ws.send(
          JSON.stringify({
            type: "partial",
            text: FIXTURE_PARTIAL,
            timestamp: 0.25,
          }),
        );
      }, 250);

      ws.onMessage((message) => {
        // The page sends binary PCM frames (which we ignore) plus a
        // {"type":"stop"} text frame when the user clicks stop.
        if (typeof message !== "string") return;
        let payload;
        try {
          payload = JSON.parse(message);
        } catch {
          return;
        }
        if (payload.type === "stop") {
          setTimeout(() => {
            ws.send(
              JSON.stringify({
                type: "final",
                text: FIXTURE_FINAL,
                timestamp: 1.0,
              }),
            );
            // Server closes after flushing the final result.
            setTimeout(() => ws.close(1000, "ok"), 50);
          }, 250);
        }
      });

      ws.onClose(() => clearTimeout(partialTimer));
    });

    // ---- 5. Drive the UI.
    await page.goto(STUDENT_URL);

    // The mic button is the only role=button with the "mic" label /
    // "Start recording" aria-label.
    const micButton = page.getByRole("button", {
      name: /start recording/i,
    });
    await expect(micButton).toBeVisible();

    const t0 = Date.now();
    await micButton.click();

    // ---- 6. SLA #1: partial visible within 1500 ms.
    const partialPreview = page.getByTestId("stt-partial-preview");
    await expect(partialPreview).toContainText(FIXTURE_PARTIAL, {
      timeout: 1500,
    });
    const partialLatencyMs = Date.now() - t0;
    expect(partialLatencyMs).toBeLessThan(1500);

    // ---- 7. Click stop. After accepting, the same button's aria-
    // label flips to "Stop recording".
    const stopButton = page.getByRole("button", {
      name: /stop recording/i,
    });
    const t1 = Date.now();
    await stopButton.click();

    // ---- 8. SLA #2: final transcript lands in the answer textarea
    // within 3000 ms.
    const textarea = page.locator("textarea");
    await expect(textarea).toHaveValue(FIXTURE_FINAL, { timeout: 3000 });
    const finalLatencyMs = Date.now() - t1;
    expect(finalLatencyMs).toBeLessThan(3000);
  });
});
