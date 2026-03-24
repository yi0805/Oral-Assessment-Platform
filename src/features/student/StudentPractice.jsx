import { useState } from "react";

import StudentPracticeModal from "./StudentPracticeModal";
import ContentCard from "../../ui/ContentCard";
import Heading from "../../ui/Heading";
import InlineGroup from "../../ui/InlineGroup";
import Input from "../../ui/Input";
import Button from "../../ui/Button";

export default function StudentPractice() {
  const [courseNumber, setCourseNumber] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  function open() {
    if (!courseNumber.trim()) return;
    setIsOpen(true);
  }

  function close() {
    setIsOpen(false);
  }

  return (
    <>
      <ContentCard>
        <Heading $variant="page">Student dashboard</Heading>

        <InlineGroup>
          <Input
            value={courseNumber}
            onChange={(e) => setCourseNumber(e.target.value)}
            placeholder="Enter course number"
          />
          <Button className="btn-fill-effect" type="button" onClick={open}>
                      Start AI practice 
          </Button>
        </InlineGroup>
      </ContentCard>

      <StudentPracticeModal
        isOpen={isOpen}
        onClose={close}
        courseNumber={courseNumber}
      />
    </>
  );
}
