export function buildQuestionBlocks(transcript) {
  const blocks = [];

  let currentMainBlock = null;
  let currentFollowup = null;

  for (const index of transcript) {
    if (index.message_type === "main_question") {
      currentMainBlock = {
        question: index.content,
        answer: "",
        sequenceNo: index.sequence_no,
        followups: [],
      };

      blocks.push(currentMainBlock);
      currentFollowup = null;
    } else if (index.message_type === "followup_question") {
      if (!currentMainBlock) continue;

      currentFollowup = {
        question: index.content,
        answer: "",
        sequenceNo: index.sequence_no,
      };

      currentMainBlock.followups.push(currentFollowup);
    } else if (index.message_type === "student_answer") {
      if (currentFollowup) {
        currentFollowup.answer = index.content;
        currentFollowup = null;
      } else if (currentMainBlock) {
        currentMainBlock.answer = index.content;
      }
    }
  }

  return blocks;
}
