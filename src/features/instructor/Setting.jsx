import { useEffect, useState, useQueryClient } from "react";
import Spinner from "../../ui/Spinner";
import { NavLink } from "react-router";

import { useUser } from "../authentication/useUser";
import { useUpdateName } from "./useUpdateName";

export default function Setting() {
  const [upi, setUPI] = useState("");
  const [displayName, setDisplayName] = useState("");

  const { user, isLoading } = useUser();
  const { updateName, isPending } = useUpdateName();

  const userUPI = user?.upi || user?.email?.split("@")[0] || "N/A";

  useEffect(() => {
    if (user?.full_name) setDisplayName(user.full_name);
  }, [user]);

  if (isLoading) return <Spinner />;

  const handleUpdateName = () => {
    if (!displayName.trim()) return;
    updateName(displayName);
  };

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <div className="mb-10">
          <NavLink
            className="group mb-4 inline-flex items-center gap-2 text-xs font-bold text-outline-variant transition-colors hover:text-primary"
            to="/home"
          >
            <span className="material-symbols-outlined text-sm transition-transform group-hover:-translate-x-1">
              arrow_back
            </span>

            <span className="font-body uppercase tracking-widest">
              Back to Courses
            </span>
          </NavLink>

          <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
            Settings
          </h1>

          <p className="mt-2 text-sm text-on-surface-variant">
            Update your personal details and access platform information.
          </p>
        </div>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
            <span
              className="material-symbols-outlined text-primary"
              data-icon="school"
              style={{ verticalAlign: "middle" }}
            >
              person
            </span>
            General
          </h2>

          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  Profile Picture
                </label>
                <img
                  alt="User profile avatar"
                  className="h-30 w-30 rounded-full object-cover"
                  referrerPolicy="no-referrer"
                  src={user?.image || "/WhereRU.png"}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  Edit Your Display Name
                </label>
                <div className="flex gap-4">
                  <input
                    className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 focus:ring-primary/20"
                    type="text"
                    onChange={(e) => setDisplayName(e.target.value)}
                    defaultValue={user?.full_name || ""}
                  />
                  <button
                    onClick={handleUpdateName}
                    disabled={isPending || displayName === user?.full_name}
                    className="rounded-xl bg-primary px-6 py-2 font-bold text-white transition-opacity disabled:opacity-50"
                  >
                    {isPending ? "Saving..." : "Save"}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  UPI (University ID)
                </label>
                <input
                  disabled
                  className="w-full cursor-not-allowed rounded-xl border-none bg-surface-container px-4 py-3 text-outline"
                  value={user?.upi || ""}
                />
              </div>
            </div>
          </div>
        </section>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
            <span
              className="material-symbols-outlined text-primary"
              data-icon="school"
              style={{ verticalAlign: "middle" }}
            >
              info
            </span>
            About
          </h2>

          <div className="max-w-3xl space-y-6">
            <p className="text-mid leading-relaxed text-on-surface-variant">
              WhereRU is an AI-supported oral assessment tool designed to
              streamline oral assessment workflows. By leveraging intelligent
              process management, we provide instructors and students with a
              more precise, efficient, and interactive evaluation experience.
            </p>

            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-outline">
                Development Team - Team 8 Next Level
              </h3>

              <div className="grid grid-cols-2 gap-4">
                {[
                  "Yihuan Tang",
                  "Whilin Zhao",
                  "Joanne Chen",
                  "Bess Zhang",
                  "James Wilner",
                  "Henry Song",
                ].map((member) => (
                  <div
                    key={member}
                    className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-low p-3"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-secondary">
                      <span className="material-symbols-outlined text-lg">
                        groups
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-on-surface">
                      {member}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-outline-variant/20 pt-4">
              <p className="text-[13px] italic text-outline">
                Supervised by: Shyamli Sindhwani, Anna Trofimova
              </p>
              <span className="font-mono text-[12px] text-outline">v1.0.2</span>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
