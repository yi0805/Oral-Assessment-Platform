function SearchCouse({ value, onChange }) {
  return (
    <div className="group relative">
      <input
        className="w-full rounded-xl border-none bg-surface-container-lowest py-3 pl-11 pr-4 text-sm ring-1 ring-outline-variant/20 transition-all focus:ring-primary/40"
        placeholder="Find a course..."
        value={value}
        onChange={onChange}
        type="text"
      />

      <span
        className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant transition-colors group-focus-within:text-primary"
        data-icon="search"
      >
        search
      </span>
    </div>
  );
}

export default SearchCouse;
