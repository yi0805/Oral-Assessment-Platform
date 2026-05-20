import { useState } from "react";
import { useNavigate } from "react-router";

import { useLogout } from "../features/authentication/useLogout";
import { useUser } from "../features/authentication/useUser";
import { useNotifications } from "../features/instructor/useNotifications";
import { useMarkNotificationRead } from "../features/instructor/useMarkNotificationRead";
import { useMarkAllNotificationsRead } from "../features/instructor/useMarkAllNotificationsRead";
import { useJoinRequests } from "../features/instructor/useJoinRequests";
import { useApproveJoinRequest } from "../features/instructor/useApproveJoinRequest";
import { useRejectJoinRequest } from "../features/instructor/useRejectJoinRequest";
import { useDismissJoinRequest } from "../features/instructor/useDismissJoinRequest";
import { formatTermLabel } from "../utils/constants";

function Header() {
  const { user } = useUser();
  const { logout } = useLogout();
  const navigate = useNavigate();

  const [helper, setHelper] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const isInstructor = user?.role === "instructor";

  const { notifications } = useNotifications({ enabled: isInstructor });
  const { markRead } = useMarkNotificationRead();
  const { markAllRead } = useMarkAllNotificationsRead();

  const { pendingForReview, myPending, myResults } = useJoinRequests({
    enabled: isInstructor,
  });
  const { approve, isPending: isApproving } = useApproveJoinRequest();
  const { reject, isPending: isRejecting } = useRejectJoinRequest();
  const { dismiss, isPending: isDismissing } = useDismissJoinRequest();

  const blurAlertCount = notifications.length;
  const pendingReviewCount = pendingForReview.length;
  const myPendingCount = myPending.length;
  const myResultsCount = myResults.length;
  const totalCount =
    blurAlertCount + pendingReviewCount + myPendingCount + myResultsCount;
  const hasAnyNotification = totalCount > 0;

  function handleOpenNotification(notification) {
    markRead(notification.id);
    setShowNotifications(false);
    navigate(`/instructor/transcript/${notification.session_id}`);
  }

  function handleDismissBlurAlert(event, notificationId) {
    event.stopPropagation();
    markRead(notificationId);
  }

  function handleMarkAll() {
    markAllRead();
  }

  return (
    <>
      {helper && (
        <div className="fixed right-[280px] top-14 z-50 flex">
          <div className="before:z-60 relative max-w-60 rounded-2xl bg-surface-container-lowest py-5 pl-5 pr-1 shadow-md before:absolute before:-top-[18px] before:right-5 before:h-0 before:w-0 before:border-b-[18px] before:border-l-[14px] before:border-r-[14px] before:border-b-surface-container-lowest before:border-l-transparent before:border-r-transparent before:content-['']">
            <button
              className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-xl bg-transparent text-sm font-semibold text-outline-variant transition-all hover:bg-surface-container"
              onClick={() => setHelper(false)}
            >
              <span
                className="material-symbols-outlined text-[16px] text-primary"
                data-icon="close"
              >
                close
              </span>
            </button>
            <p className="text-sm">
              If any problem encountered, please contact our tech maintenance
              Yihuan Tang, ytan960@aucklanduni.ac.nz
            </p>
          </div>
        </div>
      )}

      {isInstructor && showNotifications && (
        <div className="fixed right-[320px] top-14 z-50 flex">
          <div className="before:z-60 relative w-96 rounded-2xl bg-surface-container-lowest shadow-md before:absolute before:-top-[18px] before:right-5 before:h-0 before:w-0 before:border-b-[18px] before:border-l-[14px] before:border-r-[14px] before:border-b-surface-container-lowest before:border-l-transparent before:border-r-transparent before:content-['']">
            <div className="flex items-center justify-between border-b border-outline-variant/10 px-5 py-3">
              <p className="text-sm font-semibold text-on-surface">
                Notifications
              </p>

              <div className="flex items-center gap-2">
                {blurAlertCount > 0 && (
                  <button
                    className="rounded-md px-2 py-1 text-xs font-semibold text-primary transition-colors hover:bg-primary/5"
                    onClick={handleMarkAll}
                  >
                    Mark all as read
                  </button>
                )}

                <button
                  className="flex h-5 w-5 items-center justify-center rounded-xl bg-transparent text-outline-variant transition-all hover:bg-surface-container"
                  onClick={() => setShowNotifications(false)}
                >
                  <span
                    className="material-symbols-outlined text-[16px] text-primary"
                    data-icon="close"
                  >
                    close
                  </span>
                </button>
              </div>
            </div>

            <div className="max-h-96 overflow-y-auto">
              {!hasAnyNotification && (
                <p className="px-5 py-6 text-center text-sm text-on-surface-variant">
                  No new notifications.
                </p>
              )}

              {pendingReviewCount > 0 && (
                <>
                  <p className="px-5 pb-1 pt-3 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                    Join requests
                  </p>

                  {pendingForReview.map((req) => (
                    <div
                      key={req.id}
                      className="flex w-full items-start gap-3 border-b border-outline-variant/5 px-5 py-3"
                    >
                      <span
                        className="material-symbols-outlined mt-0.5 text-primary"
                        data-icon="person_add"
                      >
                        person_add
                      </span>

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-on-surface">
                          {req.requester_full_name}
                        </p>

                        <p className="truncate text-xs text-on-surface-variant">
                          {req.course_code} · {formatTermLabel(req.term)}
                        </p>

                        <p className="mt-1 text-xs text-on-surface-variant">
                          requests to join as instructor
                        </p>

                        <div className="mt-2 flex gap-2">
                          <button
                            className="rounded-md bg-primary px-3 py-1 text-xs font-bold text-on-primary transition-colors hover:bg-primary-dim disabled:opacity-50"
                            onClick={() => approve(req.id)}
                            disabled={isApproving || isRejecting}
                          >
                            Approve
                          </button>

                          <button
                            className="rounded-md border border-outline-variant/30 px-3 py-1 text-xs font-bold text-on-surface-variant transition-colors hover:bg-surface-container disabled:opacity-50"
                            onClick={() => reject(req.id)}
                            disabled={isApproving || isRejecting}
                          >
                            Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </>
              )}

              {(myPendingCount > 0 || myResultsCount > 0) && (
                <>
                  <p className="px-5 pb-1 pt-3 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                    My requests
                  </p>

                  {myPending.map((req) => (
                    <div
                      key={req.id}
                      className="flex w-full items-start gap-3 border-b border-outline-variant/5 px-5 py-3"
                    >
                      <span
                        className="material-symbols-outlined mt-0.5 text-on-surface-variant"
                        data-icon="hourglass_empty"
                      >
                        hourglass_empty
                      </span>

                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-semibold text-on-surface">
                          Request pending
                        </p>

                        <p className="truncate text-xs text-on-surface-variant">
                          {req.course_code} · {formatTermLabel(req.term)}
                        </p>

                        <p className="mt-1 text-xs text-on-surface-variant">
                          Awaiting response from the original instructor
                        </p>
                      </div>
                    </div>
                  ))}

                  {myResults.map((req) => {
                    const approved = req.status === "approved";

                    return (
                      <div
                        key={req.id}
                        className="flex w-full items-start gap-3 border-b border-outline-variant/5 px-5 py-3"
                      >
                        <span
                          className={`material-symbols-outlined mt-0.5 ${approved ? "text-primary" : "text-error"}`}
                          data-icon={approved ? "check_circle" : "cancel"}
                        >
                          {approved ? "check_circle" : "cancel"}
                        </span>

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-semibold text-on-surface">
                            Your request was {req.status}
                          </p>

                          <p className="truncate text-xs text-on-surface-variant">
                            {req.course_code} · {formatTermLabel(req.term)}
                          </p>
                        </div>

                        <button
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-outline-variant transition-colors hover:bg-surface-container-highest disabled:opacity-50"
                          onClick={() => dismiss(req.id)}
                          disabled={isDismissing}
                          aria-label="Dismiss notification"
                        >
                          <span
                            className="material-symbols-outlined text-[16px]"
                            data-icon="close"
                          >
                            close
                          </span>
                        </button>
                      </div>
                    );
                  })}
                </>
              )}

              {blurAlertCount > 0 && (
                <>
                  <p className="px-5 pb-1 pt-3 text-[10px] font-bold uppercase tracking-[0.15em] text-on-surface-variant">
                    Submissions
                  </p>

                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className="flex w-full items-start gap-3 border-b border-outline-variant/5 px-5 py-3 transition-colors hover:bg-surface-container"
                    >
                      <button
                        className="flex min-w-0 flex-1 items-start gap-3 text-left"
                        onClick={() => handleOpenNotification(n)}
                      >
                        <span
                          className="material-symbols-outlined mt-0.5 text-error"
                          data-icon="warning"
                        >
                          warning
                        </span>

                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-semibold text-on-surface">
                            {n.student_name}
                          </p>

                          <p className="truncate text-xs text-on-surface-variant">
                            {n.course_code} · {n.assessment_title}
                          </p>

                          <p className="mt-1 text-xs text-error">
                            Possible cheating · {n.blur_count} tab switches
                          </p>
                        </div>
                      </button>

                      <button
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-outline-variant transition-colors hover:bg-surface-container-highest"
                        onClick={(e) => handleDismissBlurAlert(e, n.id)}
                        aria-label="Dismiss notification"
                      >
                        <span
                          className="material-symbols-outlined text-[16px]"
                          data-icon="close"
                        >
                          close
                        </span>
                      </button>
                    </div>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      <header className="fixed top-0 z-40 flex h-16 w-full items-center justify-between bg-[#f8f9fa] px-8 dark:bg-slate-900">
        <button
          className="flex items-center gap-8 transition-transform duration-200 hover:scale-110"
          onClick={() => {
            navigate("/home");
          }}
        >
          <span className="headline-font text-xl font-bold tracking-tight text-[#4f6073] dark:text-white">
            WhereRU
          </span>
        </button>
        <div className="flex items-center gap-4">
          <div className="mr-4 flex gap-2">
            {isInstructor && (
              <button
                className="relative rounded-full p-2 text-[#4f6073] transition-colors duration-200 hover:bg-[#eaeff1] active:scale-95"
                onClick={() => setShowNotifications((v) => !v)}
              >
                <span
                  className="material-symbols-outlined"
                  data-icon="notifications"
                >
                  notifications
                </span>

                {totalCount > 0 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-5 min-w-[20px] items-center justify-center rounded-full bg-error px-1 text-[10px] font-bold text-on-error">
                    {totalCount > 99 ? "99+" : totalCount}
                  </span>
                )}
              </button>
            )}

            <button
              className="rounded-full p-2 text-[#4f6073] transition-colors duration-200 hover:bg-[#eaeff1] active:scale-95"
              onClick={() => navigate("/setting")}
            >
              <span className="material-symbols-outlined" data-icon="settings">
                settings
              </span>
            </button>

            <button
              className="rounded-full p-2 text-[#4f6073] transition-colors duration-200 hover:bg-[#eaeff1] active:scale-95"
              onClick={() => setHelper(true)}
            >
              <span className="material-symbols-outlined" data-icon="help">
                help
              </span>
            </button>
          </div>
          <div className="flex items-center gap-3 border-l border-outline-variant/20 pl-4">
            <div className="hidden text-right sm:block">
              <p className="headline-font text-sm font-semibold text-on-surface">
                {user?.full_name || "User"}
              </p>
              <p className="text-xs text-on-surface-variant">
                {user?.role || "Role"}
              </p>
            </div>
            <img
              alt="User profile avatar"
              className="h-10 w-10 rounded-full object-cover"
              data-alt="portrait of a young man with short brown hair and a friendly smile, clean-shaven, wearing a light blue oxford shirt in soft indoor lighting"
              referrerPolicy="no-referrer"
              src={user?.image || "/WhereRU.png"}
            />
            <button
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-error transition-all hover:bg-error/5 active:scale-95"
              onClick={() => logout()}
            >
              Logout
            </button>
          </div>
        </div>
      </header>
    </>
  );
}

export default Header;
