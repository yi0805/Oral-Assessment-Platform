import { NavLink } from "react-router";

import { useUser } from "../features/authentication/useUser";

function Sidebar() {
  const { user } = useUser();

  return (
    <aside className="fixed left-0 top-0 z-30 hidden h-screen w-64 flex-col gap-y-2 bg-[#eaeff1] pr-4 pt-20 dark:bg-slate-800/50 md:flex">
      <div className="mb-8 mt-4 px-6">
        <div className="mb-2 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-on-primary">
            <img
              src="/WhereRU.png"
              alt="WhereRU logo"
              className="h-8 w-8 object-contain"
            />
          </div>
          {user.role === "instructor" ? (
            <div>
              <h2 className="font-['Manrope'] font-bold leading-tight text-[#4f6073] dark:text-white">
                Instructor Portal
              </h2>
              <p className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                Academic Management
              </p>
            </div>
          ) : (
            <div>
              <h2 className="font-['Manrope'] font-bold leading-tight text-[#4f6073] dark:text-white">
                Student Portal
              </h2>
              <p className="text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
                Academic Engagement
              </p>
            </div>
          )}
        </div>
      </div>
      <nav className="flex flex-col gap-y-1">
        <NavLink
          className={({ isActive }) =>
            `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${
              isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" 
              : "rounded-r-full text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
          }
          to="/home"
        >
          <span
            className="material-symbols-outlined text-[20px]"
            data-icon="school"
          >
            school
          </span>
          <span>Courses</span>
        </NavLink>
        {user.role === "student" && (
          <NavLink
            className={({ isActive }) =>
            `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${
              isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" 
              : "rounded-r-full text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
          }
            to="/student/previousAssessments"
          >
            <span
              className="material-symbols-outlined text-[20px]"
              data-icon="history"
            >
              history
            </span>
            <span>Previous Assessments</span>
          </NavLink>
        )}
        {user.role === "instructor" && (
          <NavLink
          className={({ isActive }) =>
            `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${
              isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" 
              : "rounded-r-full text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
            }
            to="/instructor/studentManagement"
            >
            <span
              className="material-symbols-outlined text-[20px]"
              data-icon="people"
              >
              people
            </span>
            <span>Users & Records</span>
          </NavLink>
        )}
        {user.role === "instructor" && (
          <NavLink
            className={({ isActive }) =>
            `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${
              isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" 
              : "rounded-r-full text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
          }
            to="/instructor/updateMaterial"
          >
            <span
              className="material-symbols-outlined text-[20px]"
              data-icon="add"
            >
              add
            </span>
            <span>Generate Assessment</span>
          </NavLink>
        )}
        {user.role === "instructor" && (
          <NavLink
            className={({ isActive }) =>
            `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${
              isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" 
              : "rounded-r-full text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
          }
            to="/instructor/editAssessment"
          >
            <span
              className="material-symbols-outlined text-[20px]"
              data-icon="edit_note"
            >
              edit_note
            </span>
            <span>Edit Assessment</span>
          </NavLink>
        )}
        <NavLink
          className={({ isActive }) =>
          `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${
            isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" 
            : "rounded-r-full text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
          }
          to="/instructor/setting"
        >
          <span
            className="material-symbols-outlined text-[20px]"
            data-icon="settings"
          >
            settings
          </span>
          <span>Setting</span>
        </NavLink>
        
      </nav>
    </aside>
  );
}

export default Sidebar;
