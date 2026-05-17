import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
  
export default function DateTimePicker({
  label,
  value,
  onChange,
  minDate,
  disabled = false,
}) {
  return (
    <div>
      <label className="ml-1 block text-sm font-semibold text-on-surface-variant">
        {label}
      </label>

      <DatePicker
        selected={value}
        onChange={onChange}
        showTimeSelect
        timeIntervals={1}
        dateFormat="yyyy-MM-dd HH:mm"
        minDate={minDate ? minDate : new Date()}
        placeholderText="Select date & time"
        disabled={disabled}
        className="block w-full rounded-xl border-none bg-surface-container-low px-4 py-3 text-on-surface transition-all focus:ring-2 text-sm shadow-xs disabled:cursor-not-allowed disabled:opacity-60"
      />
    </div>
  );
}