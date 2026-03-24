import styled from "styled-components";

import Input from "./Input";

const SearchInput = styled(Input)`
  width: 100%;
  max-width: 480px;
`;

export default function SearchBar({
  value,
  onChange,
  placeholder = "Search...",
  ...props
}) {
  return (
    <SearchInput
      type="search"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      {...props}
    />
  );
}
