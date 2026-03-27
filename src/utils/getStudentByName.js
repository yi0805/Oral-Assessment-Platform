import mockStudents from "../data/mockStudents";

function getStudentByName(userName) {
  return mockStudents.find((student) => student.username === userName);
}

export default getStudentByName;
