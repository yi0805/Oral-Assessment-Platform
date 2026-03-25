import { SearchField, Label, Description, FieldError } from "@heroui/react";

function SearchInstructor() {
  return (
    <SearchField>
      <Label />
      <SearchField.Group className="w-[50%] max-w-[50ch]">
        <SearchField.SearchIcon />
        <SearchField.Input />
        <SearchField.ClearButton />
      </SearchField.Group>
      <Description />
      <FieldError />
    </SearchField>
  );
}

export default SearchInstructor;
