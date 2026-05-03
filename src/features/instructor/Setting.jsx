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
          <div className="mb-6 flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <span className="material-symbols-outlined text-xl">person</span>
            </div>

            <div>
              <h2 className="text-xl font-bold text-on-surface">General</h2>

              <p className="mt-1 max-w-md text-xs text-on-surface-variant">
                Update your profile and avatar.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-[auto_1fr] items-start gap-x-10 gap-y-8">
            <div>
              <label className="mb-3 ml-1 block text-sm font-semibold text-on-surface-variant">
                Profile Picture
              </label>

              <button
                type="button"
                onClick={handleImageClick}
                disabled={isUpdatingPic}
                className="group relative h-24 w-24 rounded-full transition-all duration-200 hover:ring-4 hover:ring-primary/15 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-primary/40 disabled:cursor-not-allowed"
              >
                <div
                  className={`h-24 w-24 overflow-hidden rounded-full border-2 border-surface-container transition-all group-hover:border-primary/30 ${
                    isUpdatingPic ? "opacity-50" : ""
                  }`}
                >
                  <img
                    src={user?.image || "/WhereRU.png"}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    alt="Profile"
                  />
                </div>

                <span className="pointer-events-none absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full border border-outline-variant/30 bg-surface-container-lowest text-on-surface shadow-[0_2px_8px_rgba(0,0,0,0.15)] transition-all group-hover:border-primary group-hover:bg-primary group-hover:text-on-primary">
                  <span className="material-symbols-outlined text-xl">
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
            </div>

            <div className="max-w-xl space-y-6">
              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  UPI (University ID)
                </label>

                <div className="relative">
                  <input
                    disabled
                    className="w-full cursor-not-allowed rounded-xl border-none bg-surface-container-low px-4 py-3 pr-11 text-on-surface-variant"
                    value={user?.upi || ""}
                  />

                  <span className="material-symbols-outlined pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-base text-outline">
                    lock
                  </span>
                </div>
                <p className="ml-1 text-[11px] text-outline">
                  Issued by your institution.
                </p>
              </div>

              <div className="space-y-2">
                <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
                  Display Name
                </label>
                <input
                  className="w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all placeholder:text-outline focus:ring-2 focus:ring-primary/20"
                  type="text"
                  onChange={(e) => setDisplayName(e.target.value)}
                  value={displayName}
                />

                <div className="flex justify-end pt-1">
                  <button
                    onClick={handleUpdateName}
                    disabled={isPending || !isNameDirty}
                    className="rounded-xl bg-primary px-6 py-2.5 text-sm font-bold tracking-tight text-on-primary shadow-lg shadow-primary/20 transition-all hover:bg-primary-dim active:scale-[0.98] disabled:cursor-not-allowed disabled:bg-surface-container-high disabled:text-outline disabled:shadow-none disabled:active:scale-100"
                  >
                    {isPending ? "Saving..." : "Save"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <div className="mb-6 flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <span className="material-symbols-outlined text-xl">info</span>
            </div>

            <div>
              <h2 className="text-xl font-bold text-on-surface">
                About WhereRU
              </h2>

              <p className="mt-1 max-w-md text-xs text-on-surface-variant">
                Information about WhereRU and the team behind it.
              </p>
            </div>
          </div>

          <div className="max-w-2xl space-y-6">
            <p className="border-l-2 border-primary/30 pl-4 text-sm leading-relaxed text-on-surface-variant">
              WhereRU is an AI-supported oral assessment tool designed to
              streamline oral assessment workflows. By leveraging intelligent
              process management, we provide instructors and students with a
              more precise, efficient, and interactive evaluation experience.
            </p>

            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-on-surface-variant">
                Development Team — Team 8 Next Level
              </h3>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {teamMembers.map((member, i) => (
                  <div
                    key={member}
                    className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-low p-3 transition-colors hover:bg-surface-container"
                  >
                    <div
                      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                        ImageColors[i % ImageColors.length]
                      }`}
                    >
                      {getInitials(member)}
                    </div>

                    <span className="text-sm font-semibold text-on-surface">
                      {member}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-outline-variant/20 pt-4">
              <p className="text-[13px] italic text-outline">
                Supervised by Shyamli Sindhwani & Anna Trofimova
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
