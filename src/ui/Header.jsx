import styled from "styled-components";

import UserAvatar from "./UserAvatar";

const StyledHeader = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-light);
  border-bottom: 1px solid var(--color-light-2);
  padding: var(--space-xl) var(--space-3xl);
  grid-area: header;
`;

const Brand = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-2xs);
`;

const Title = styled.h1`
  font-size: var(--font-size-xl);
  color: var(--color-primary);
  line-height: 1.1;
`;

const Logo = styled.img`
  width: 4rem;
  height: 2rem;
`;

function Header() {
  return (
    <StyledHeader>
      <Brand>
        <Title>WhereAU</Title>
        <Logo src="xxx" alt="WhereAU Logo" />
      </Brand>
      <UserAvatar />
    </StyledHeader>
  );
}

export default Header;
