function getEarliestAssessment(assessments) {
  const earliestAssessment = assessments.reduce((earliest, current) => {
    const earliestDate = new Date(earliest.deadline);
    const currentDate = new Date(current.deadline);

    return currentDate < earliestDate ? current : earliest;
  });

  const earliestDeadline = earliestAssessment.deadline;

  return earliestDeadline;
}

export default getEarliestAssessment;
