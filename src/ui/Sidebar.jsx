import styled from "styled-components";
import { NavLink } from "react-router";

import useRequireAuth from "../hooks/useRequireAuth";
import UpdateMaterial from "../features/instructor/UploadMaterial";

const StyledSidebar = styled.div`
  background: var(--color-light);
  border-right: 1px solid var(--color-light-2);
  padding: var(--space-3xl) var(--space-xl);
  min-height: 90%;
  grid-area: sidebar;
  border-radius: 12px;
  margin: 10px 5px;

  @media (max-width: 768px) {
    min-height: auto;
    border-right: none;
    border-bottom: 1px solid var(--color-light-2);
    padding: var(--space-m) var(--space-xl);
  }
`;

const Nav = styled.nav`
  display: flex;
  flex-direction: column;
  gap: var(--space-m);

  @media (max-width: 768px) {
    flex-direction: row;
  }
`;

const Item = styled(NavLink)`
  text-decoration: none;
  color: var(--color-dark-2);
  padding: var(--space-m) var(--space-l);
  border-radius: var(--radius-md);

  &:hover:not(.active) {
    background: var(--color-primary-tint);
  }

  &.active {
    background: var(--color-secondary-tint);
    color: var(--color-primary);
    font-weight: 700;
  }
`;

function Sidebar() {
  const role = useRequireAuth();

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
          {role === "instructor" ? (
            <div>
              <h2 className="font-['Manrope'] font-bold leading-tight text-[#4f6073] dark:text-white">
                Curator Portal
              </h2>
              <p className="text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
                Academic Management
              </p>
            </div>
          ) : (
            <div>
              <h2 className="font-['Manrope'] font-bold leading-tight text-[#4f6073] dark:text-white">
                Portal
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
            `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" : "text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
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
        {role === "student" && (
          <NavLink
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" : "text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
            }
            to="/student/previous-assessments"
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
        {role === "instructor" && (
          <NavLink
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium transition-all duration-300 ease-in-out dark:text-slate-400 dark:hover:bg-slate-700/50 ${isActive ? "rounded-r-full bg-white text-[#4f6073] shadow-sm dark:bg-slate-700 dark:text-white" : "text-[#586064] hover:bg-white/50 hover:text-[#4f6073]"}`
            }
            to="/instructor/update-material"
          >
            <span
              className="material-symbols-outlined text-[20px]"
              data-icon="edit_note"
            >
              edit_note
            </span>
            <span>Update Material</span>
          </NavLink>
        )}
        <a
          className="flex items-center gap-3 px-6 py-3 font-['Inter'] text-sm font-medium text-[#586064] transition-all hover:bg-white/50 hover:text-[#4f6073] dark:text-slate-400 dark:hover:bg-slate-700/50"
          href=""
        >
          <span
            className="material-symbols-outlined text-[20px]"
            data-icon="settings"
          >
            settings
          </span>
          <span>Settings</span>
        </a>
      </nav>
    </aside>
  );
}

export default Sidebar;
