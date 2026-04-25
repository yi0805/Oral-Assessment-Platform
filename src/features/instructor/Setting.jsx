import { useEffect, useState, useRef } from "react";
import Spinner from "../../ui/Spinner";
import { NavLink } from "react-router";

import { useUser } from "../authentication/useUser";
import { useUpdateName } from "./useUpdateName";
import { useUpdatePicture } from "./useUpdatePicture";


export default function Setting(){
  const [upi, setUPI] = useState("");
  const [displayName, setDisplayName] = useState("");

  const { user, isLoading } = useUser();
  const { updateName, isPending } = useUpdateName();
  const { uploadFile, isUpdatingPic } = useUpdatePicture();
  
  const userUPI = user?.upi || user?.email?.split('@')[0] || "N/A";
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user?.full_name) setDisplayName(user.full_name);
  }, [user]);

  if (isLoading) return <Spinner />;

  const handleUpdateName = () => {
      if (!displayName.trim()) return;
      updateName(displayName);
    };

  const handleImageClick = () => {
      fileInputRef.current.click();
    };  

  const handleFileChange = (e) => {
    const file = e.target.files[0]; 
    if (file) {
      uploadFile(file);
    }
  };

  return (
    <div className="min-h-screen">
      <main className="ml-64 px-10 pb-12 pt-24">
        <div className="mb-10">
          <NavLink
            className="group mb-4 inline-flex items-center gap-2 text-xs font-bold 
            text-outline-variant transition-colors hover:text-primary"
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ml-1 mb-2 block text-sm font-semibold text-on-surface-variant">
                  Edit Your Profile Picture
                </label>
                <div className="relative h-24 w-24 cursor-pointer" onClick={handleImageClick}>
                  <div className={`h-24 w-24 rounded-full overflow-hidden
                    border-2 border-surface-container ${isUpdatingPic ? 'opacity-50' : ''}`}>
                    <img 
                      src={user?.image || "/default-avatar.png"} 
                      className="h-full w-full object-cover"
                      alt="Profile" 
                    />
                  </div>
                  <button 
                    className="absolute -bottom-1 -right-1 h-8 w-8 rounded-full bg-white p-1 
                    text-black shadow-[0_2px_8px_rgba(0,0,0,0.15)] flex items-center justify-center 
                    border border-gray-100 hover:bg-gray-100 transition-colors"
                  >
                    <span className="material-symbols-outlined text-xl">
                      photo_camera
                    </span>
                  </button>
                  {isUpdatingPic && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    </div>
                  )}
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    className="hidden" 
                    accept="image/*"
                  />
                </div>

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
                    value={displayName}
                  />                  
                  <button
                    onClick={handleUpdateName}
                    disabled={isPending || displayName === user?.full_name || !displayName.trim()}
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
            <p className="text-mid text-on-surface-variant leading-relaxed">
              WhereRU is an AI-supported oral assessment tool designed to streamline oral assessment workflows. 
              By leveraging intelligent process management, we provide instructors and students with a more precise, 
              efficient, and interactive evaluation experience.
            </p>

            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-outline">
                Development Team - Team 8 Next Level
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                {["Yihuan Tang", "Whilin Zhao", "Joanne Chen", "Bess Zhang", "James Wilner", "Henry Song"].map((member) => (
                  <div key={member} className="flex items-center gap-3 rounded-xl border border-outline-variant/10 bg-surface-container-low p-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-secondary">
                      <span className="material-symbols-outlined text-lg">groups</span>
                    </div>
                    <span className="text-sm font-semibold text-on-surface">{member}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-outline-variant/20">
              <p className="text-[13px] text-outline italic">
                Supervised by: Shyamli Sindhwani, Anna Trofimova 
              </p>
              <span className="text-[12px] font-mono text-outline">v1.0.2</span>
            </div>
          </div> 
        </section>

      </main>
    </div>
    );
}
