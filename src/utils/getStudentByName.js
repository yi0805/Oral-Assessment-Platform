import mockStudents from "../data/mockStudents";

function getStudentByName(userName) {
  return mockStudents.find((student) => student.studentName === userName);
}

export default getStudentByName;
