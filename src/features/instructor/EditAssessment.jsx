import { useEffect, useState, useRef } from "react";
import Spinner from "../../ui/Spinner";
import { NavLink } from "react-router";

export default function EditAssessment(){

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
            Edit Assessment
          </h1>

          <p className="mt-2 text-sm text-on-surface-variant">
            Update the assessment details.
          </p>
        </div>

        <section className="mb-8 rounded-xl bg-surface-container-lowest p-8 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.04)]">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold">
            <span
              className="material-symbols-outlined text-primary"
              data-icon="school"
              style={{ verticalAlign: "middle" }}
            >
              description
            </span>
            Assessment Parameters
          </h2>
        </section>
      </main>
    </div>
  );
}
