import styled from "styled-components";

import UserAvatar from "./UserAvatar";

const StyledHeader = styled.header`
  display: flex;
  align-items: center;
  background-color: blue;
  padding: 1rem;
  grid-area: header;
`;

const H1 = styled.h1`
  text-align: center;
`;

function Header() {
  return (
    <StyledHeader>
      <H1>Header Here</H1>
      <UserAvatar />
    </StyledHeader>
  );
}

export default Header;
