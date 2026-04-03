import { useLogout } from "../features/authentication/useLogout";
import { useUser } from "../features/authentication/useUser";
import Loading from "../ui/Loading";

function Header() {
  const { user } = useUser();
  const { logout, isPending } = useLogout();

  if (isPending) return <Loading />;

  return (
    <header className="fixed top-0 z-40 flex h-16 w-full items-center justify-between bg-[#f8f9fa] px-8 dark:bg-slate-900">
      <div className="flex items-center gap-8">
        <span className="headline-font text-xl font-bold tracking-tight text-[#4f6073] dark:text-white">
          WhereRU
        </span>
      </div>
      <div className="flex items-center gap-4">
        <div className="mr-4 flex gap-2">
          <button className="rounded-full p-2 text-[#4f6073] transition-colors duration-200 hover:bg-[#eaeff1] active:scale-95">
            <span
              className="material-symbols-outlined"
              data-icon="notifications"
            >
              notifications
            </span>
          </button>
          <button className="rounded-full p-2 text-[#4f6073] transition-colors duration-200 hover:bg-[#eaeff1] active:scale-95">
            <span className="material-symbols-outlined" data-icon="help">
              help
            </span>
          </button>
        </div>
        <div className="flex items-center gap-3 border-l border-outline-variant/20 pl-4">
          <div className="hidden text-right sm:block">
            <p className="headline-font text-sm font-semibold text-on-surface">
              {user.full_name || "User"}
            </p>
            <p className="text-xs text-on-surface-variant">
              {user.role || "Role"}
            </p>
          </div>
          <img
            alt="User profile avatar"
            className="h-10 w-10 rounded-full object-cover"
            data-alt="portrait of a young man with short brown hair and a friendly smile, clean-shaven, wearing a light blue oxford shirt in soft indoor lighting"
            referrerPolicy="no-referrer"
            src={user.image || "/WhereRU.png"}
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
  );
}

export default Header;
