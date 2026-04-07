import { useNavigate } from "react-router";

function CourseCard({ courseId, courseCode, courseName, index, description }) {
  const navigate = useNavigate();

  const images = [
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDfgr_pP5i7hQoboiS_DsxFRPWBpPHlHpUXumClpddDt2JX7BsTy1RucSS9hAnXPHskftAHFN-qV7kXv61MwoKaNkxvqx41RxJsHnItt2OmhV9TcIGhNkjwwWJDIJBpGx1OVaevsdmzLdL53qdnBksk7Ks2vMWDlbrBRf0JdHg25PrboJ2OYXhx8vTxAta6zZTLt7dT2JXlzV-OxVl6RPR0-L5aXHJxzBKh-c8MTw86BqkmHDoPdgqjbfQS5aA-OmT8pNhuXzlc9KnW",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuB_TjDjVsjnTlwmwB0gDWQ-U-AahXp_b8lpZ14Py7eMk63zOzkUqUQY-fl84SbQNLlfXPTSiOIRYU2xEJifhcY4N89ZTCr_TgabEFJOIB3cWQ6Z3jbHwc1PgxOq1jlbQ8iDTpIqVZygzlUnDqyjLMls7D0mxC5SVAM72ouBfbQxbsry7nnfEvvz4N_98td94vnn2IeNKd1h7VtcH-K_2IxLA3Oyj9lJSAjpyhlIt1Q2PNLzsuWcShb3aU5ul55WCaN6KbiRdFrrKkwr",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuBkdEcmqThK9dB3ArCqjwxvzz0_opItvI_4i5g5B7fE9L9qJWK4DObWAy-H_so9vgD-23qb2yHLjtLT9BFh8XFyu04NVBfRxEjOqvlsjG3M9Tp-oMfFMp3zlWeSnECBfU5vCdos9eKFWh-_NoPZekYd2X7W54Bx7_PW4XYDBzoIZO3qPpmkeTUlMHXH2wQV1sjNGM9M4JUfQFKSxVpQ4edkqmDEPnWfGhBSdPhq-DcrNyUu3HFuMvugK6n5-f_mGHhyk5M-V3F7jXAS",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuD3shRtSi9buB-3A-lLTQ-XDY7NQG2J-VCj0tz2hARiNzaRoOFQrXO9Wl68MzBMooDvHYVyHO_AFPzg-dzGNVkNiWxfHaCW5dK13_iHPu2I1ShEejxdAYAe4Jnmr4FWg-mgmZKoifN0QGfj5cBQNLdYT2deMzRZY2xM_a-Y8SbUmZHORRYEYRhk9R6f0TbxWHcn4IZ0YmXGfhHXADRdSOMKeCtdWd57cobtYtdTZKLkprfY_hZlHhTroGscGQlV6tj67fIz5x3pPsoA",
  ];

  const image = images[index % images.length];

  return (
    <button
      className="group flex flex-col overflow-hidden rounded-xl bg-surface-container-lowest shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)] transition-all hover:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.08)]"
      onClick={() => navigate(`/student/${courseId}`)}
    >
      <div className="relative h-48 overflow-hidden">
        <img
          alt="Advanced Molecular Biology"
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          data-alt="dramatic close-up of a double helix dna structure glowing in cool blue and violet tones with soft bokeh particles in a laboratory setting"
          src={image}
        />
        <div className="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-primary shadow-sm backdrop-blur-md">
          {courseCode}
        </div>
      </div>
      <div className="flex flex-grow flex-col p-6">
        <h3 className="headline-font mb-2 text-xl font-bold text-on-surface transition-colors group-hover:text-primary">
          {courseName}
        </h3>
        <p className="mb-6 flex-grow text-sm leading-relaxed text-on-surface-variant">
          {description}
        </p>
        {/* <div className="mt-auto flex items-center justify-between border-t border-surface-container pt-6">
          <button
            className="group/btn flex items-center gap-1 text-sm font-semibold text-primary"
            onClick={() =>
              navigate(`/student/${courseId}`, {
                state: {
                  studentName,
                  courseId,
                },
              })
            }
          >
            View Course
            <span
              className="material-symbols-outlined text-[18px] transition-transform group-hover/btn:translate-x-1"
              data-icon="arrow_forward"
            >
              arrow_forward
            </span>
          </button>
        </div> */}
      </div>
    </button>
  );
}

export default CourseCard;
