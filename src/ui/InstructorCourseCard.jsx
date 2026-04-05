import { useNavigate } from "react-router";

function InstructorCourseCard({ courses }) {
  const navigate = useNavigate();

  const images = [
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDLbme1-qtM-UiAbbRFvXko7Ur40IJU1CBzy3M3WHfExnXfRas6WWB04oszNzkn0HIuIQqS95c0mvlebbnGtYYO7g1P_aKSA4_eo8JxtbzCni53M6QEMqFFm_Cpc4k4tR2VRuS2xq_JvfHWyyfbOBdKJBFovrjTHxTlBWnp9o3X5dVGN3QIXrgZ5KbGFEuLn6l13JL7-rYWoW4OA7lvh9w9C30C_hUWpOKEnJV6A-_tyaYBGPQn9-PchQud7QYn1QVyWuVaXBoY9VFk",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDTOu3Dzu3cuVpSRAaefBBSxxHwNUbmxFuYcMo9VAGnvrHYM9jkJb3FoNoss4jcgzJOsuHdN_k9Fj88s7sgP1lFbshtlPk_rx-p5dOAiF21Y1W5Cwty1SwotPpDF8hJPhK_AZsSWC6z2l6HIRgKYgA5T4hsByIHYYvNlg-rhWmOEojDKpcTUEAb0FsDG7rOLeFyh4U-CKwFCGwKLAaVnrNKLtTy90g7TSoFTkLF7ePuYFsE4LyH3_SLY1jWpTw2jtbQBavSA965UPRi",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBTERHM07ipoDElOL12YKTeO5EO5RM2m4fhuDOINNzWTqoaMcivpZ3J3oYt5kKOQYT_Xf0xoTMh4H0N8lis12lo4Vy2QUE95mzbnf-UIgHDtQNfbP2qdiS_vkmYLAUpu2t52owY-qCo9d7DElEVyhyrXYV1iISjOGpzMg2FaskwA1IQiW9Aj-npLOgX5r3dEbqKw0lM3EG-ASF1lZ5wykkN14V4yI_5GYfZ4t-NqhKr7m4doNUNsWiMibVkdYfWp8rwQit-K7r6NW6Z",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuAgFAA_G7MZo8_DTHeZvyHfjgU1sDSE3QZ1N4yTMWBImqXw7fC01fquoaVq30uM0HToFew9DmLfPhZVc85hExYA1e1HxrnQ4S8iGs82WkyeOy60aUXg7JpPPnmXlzTZ3s1muidJ34iug1xwPTOUOa4Wk3ZAghY_bAL0pr_Zwcw_MO6Pg-2VdpTqJvWKzEq-1UPugdKm-bN4-Aw1iswDIqdv2n_pv_ZaXeiULreHblh6fHSk5v7v6QUXWzNwK0fYcYjWQFGFZ7cryEF5",
  ];

  return courses.map((course, index) => (
    <button
      key={course.id}
      className="group flex flex-col overflow-hidden rounded-xl border border-outline-variant/10 bg-surface-container-lowest text-left shadow-sm transition-all duration-300 hover:shadow-xl hover:shadow-primary/5"
      onClick={() => {
        navigate(`/instructor/${course.id}`, {
          state: { course },
        });
      }}
    >
      <div className="relative h-48 overflow-hidden">
        <img
          alt={course.course_code}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          src={images[index % images.length]}
        />
        <div className="absolute right-4 top-4 rounded-full bg-white/90 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-primary backdrop-blur-md">
          Active
        </div>
      </div>

      <div className="flex flex-grow flex-col p-6">
        <span className="mb-1 font-body text-xs font-bold text-secondary-dim">
          {course.course_code}
        </span>

        <h3 className="mb-3 font-headline text-xl font-bold text-on-surface transition-colors group-hover:text-primary">
          {course.course_name}
        </h3>

        <p className="mb-6 flex-grow font-body text-sm leading-relaxed text-on-surface-variant">
          {course.description}
        </p>
      </div>
    </button>
  ));
}

export default InstructorCourseCard;
