import styled from "styled-components";
import { useNavigate } from "react-router";
import { googleLogout } from "@react-oauth/google";

import UserAvatar from "./UserAvatar";
import Button from "./Button";

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
  flex-direction: row;
  gap: var(--space-2xs);
`;

const Title = styled.h1`
  font-size: var(--font-size-xl);
  color: var(--color-primary);
`;

const Logo = styled.img`
  width: 100%;
  max-width: 9ch;
  height: 2.5rem;
`;

const UserContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-l);
`;

function Header() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("role");
    localStorage.removeItem("userName");
    localStorage.removeItem("userPicture");
    googleLogout();
    navigate("/login");
  };

  return (
    <StyledHeader>
      <Brand>
        <Logo src="/WhereRU.png" alt="WhereAU Logo" />
        <Title>WhereRU</Title>
      </Brand>
      <UserContainer>
        <UserAvatar />
        <Button $variant="secondary" onClick={handleLogout}>
          Logout
        </Button>
      </UserContainer>
    </StyledHeader>
  );
}

export default Header;
