import { Navigate, Outlet, useParams } from "react-router";
import toast from "react-hot-toast";

import { useCourses } from "../hooks/useCourses";
import Spinner from "./Spinner";

export default function InstructorCourseLayout() {
  const { courseId } = useParams();
  const { courses, isLoading } = useCourses();

  if (isLoading) return <Spinner />;

  const course = courses.find((c) => String(c.id) === String(courseId));

  if (!course) {
    toast.error("That course is not available");
    return <Navigate replace to="/home" />;
  }

  return <Outlet />;
}
