import { useEffect, useState, useRef } from "react";
import { NavLink } from "react-router";

import { useUser } from "../authentication/useUser";
import { useUpdateName } from "./useUpdateName";
import { useUpdatePicture } from "./useUpdatePicture";

import { getInitials } from "../../utils/getInitials";

import Spinner from "../../ui/Spinner";

const teamMembers = [
  "Yihuan Tang",
  "Whilin Zhao",
  "Joanne Chen",
  "Bess Zhang",
  "James Wilner",
  "Henry Song",
];

const ImageColors = [
  "bg-primary-container text-on-primary-container",
  "bg-secondary-container text-on-secondary-container",
  "bg-tertiary-container text-on-tertiary-container",
];

const MAX_PICTURE_BYTES = 5 * 1024 * 1024;

export default function Setting() {
  const [displayName, setDisplayName] = useState("");

  const { user, isLoading } = useUser();
  const { updateName, isPending } = useUpdateName();
  const { uploadFile, isUpdatingPic } = useUpdatePicture();

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user?.full_name) setDisplayName(user.full_name);
  }, [user]);

  if (isLoading) return <Spinner />;

  const trimmedName = displayName.trim();
  const isNameDirty = trimmedName.length > 0 && trimmedName !== user?.full_name;

  const handleUpdateName = () => {
    if (!isNameDirty) return;

    updateName(trimmedName);
  };

  const handleImageClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    e.target.value = "";

    if (!file) return;

    if (!file.type.startsWith("image/")) {
      return;
    }

    if (file.size > MAX_PICTURE_BYTES) {
      return;
    }

    uploadFile(file);
  };

  return (
    <div className="min-h-screen">
      <main className="pb-12 pt-24">
        <div className="mx-auto max-w-7xl px-8">
          <div className="mb-10 max-w-5xl">
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

            <span className="mb-1 block text-xs font-bold uppercase tracking-[0.2em] text-outline">
              Account
            </span>

            <h1 className="font-headline text-4xl font-extrabold tracking-tight text-on-surface">
              Settings
            </h1>

            <p className="mt-2 text-sm text-on-surface-variant">
              Manage your profile and platform information.
            </p>
          </div>

          <section className="max-w-2xl rounded-xl bg-surface-container-lowest p-6 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={handleImageClick}
                disabled={isUpdatingPic}
                className="group relative h-14 w-14 shrink-0 rounded-full transition-all duration-200 hover:ring-4 hover:ring-primary/15 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 disabled:cursor-not-allowed"
              >
                <div
                  className={`h-14 w-14 overflow-hidden rounded-full border-2 border-surface-container transition-all group-hover:border-primary/30 ${
                    isUpdatingPic ? "opacity-50" : ""
                  }`}
                >
                  <img
                    src={user?.image || "/WhereRU.png"}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    alt="Profile"
                  />
                </div>

                <span className="pointer-events-none absolute -bottom-0.5 -right-0.5 flex h-6 w-6 items-center justify-center rounded-full border border-outline-variant/30 bg-surface-container-lowest text-on-surface shadow-[0_2px_8px_rgba(0,0,0,0.15)] transition-all group-hover:border-primary group-hover:bg-primary group-hover:text-on-primary">
                  <span className="material-symbols-outlined text-sm">
                    photo_camera
                  </span>
                </span>

                {isUpdatingPic && (
                  <div className="absolute inset-0 flex items-center justify-center rounded-full bg-on-surface/40 backdrop-blur-sm">
                    <span className="material-symbols-outlined animate-spin-slow text-on-primary">
                      progress_activity
                    </span>
                  </div>
                )}

                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                  accept="image/*"
                />
              </button>

              <div className="min-w-0 flex-1">
                <p className="truncate text-lg font-bold text-on-surface">
                  {user?.full_name || "Unnamed"}
                </p>

                <p className="mt-1 flex items-center gap-1.5 text-xs text-outline">
                  <span>UPI · {user?.upi || "—"}</span>

                  <span className="material-symbols-outlined text-sm">
                    lock
                  </span>
                </p>
              </div>
            </div>

            <div className="my-5 border-t border-outline-variant/10" />

            <div className="space-y-3">
              <label
                htmlFor="displayName"
                className="ml-1 block text-xs font-bold uppercase tracking-[0.2em] text-outline"
              >
                Display Name
              </label>

              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  id="displayName"
                  className="flex-1 rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                  type="text"
                  onChange={(e) => setDisplayName(e.target.value)}
                  value={displayName}
                />

                <button
                  onClick={handleUpdateName}
                  disabled={isPending || !isNameDirty}
                  className="shrink-0 rounded-xl bg-primary px-6 py-3 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-surface-container-high disabled:text-outline disabled:shadow-none disabled:active:scale-100"
                >
                  {isPending ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
          </section>

          <div className="mt-14 max-w-5xl">
            <div className="mb-6 flex items-center gap-4">
              <div className="h-px w-10 bg-outline-variant/40" />

              <span className="text-[11px] font-bold uppercase tracking-[0.25em] text-outline">
                About
              </span>

              <div className="h-px flex-1 bg-outline-variant/20" />
            </div>

            <p className="mb-7 max-w-2xl text-sm leading-relaxed text-on-surface-variant">
              WhereRU · AI-supported oral assessment platform for instructors
              and students.
            </p>

            <div className="mb-7">
              <p className="mb-3 text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Team 8 Next Level
              </p>

              <div className="flex flex-wrap items-center gap-2.5">
                {teamMembers.map((member, i) => (
                  <span
                    key={member}
                    title={member}
                    className={`flex h-9 w-9 cursor-default items-center justify-center rounded-full text-[11px] font-bold transition-transform hover:-translate-y-0.5 ${
                      ImageColors[i % ImageColors.length]
                    }`}
                  >
                    {getInitials(member)}
                  </span>
                ))}
              </div>
            </div>

            <p className="text-[11px] italic leading-relaxed text-outline">
              Supervised by Shyamli Sindhwani & Anna Trofimova
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
