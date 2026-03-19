import styled from "styled-components";
import { useNavigate } from "react-router";

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

const UserContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-l);
`;

const Logout = styled.button`
  border: 1px solid var(--color-light-2);
  background: var(--color-light);
  border-radius: 10px;
  padding: var(--space-s) var(--space-l);
  font-weight: 700;
  cursor: pointer;
  color: var(--color-primary);
`;

function Header() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("role");
    navigate("/login");
  };

  return (
    <StyledHeader>
      <Brand>
        <Title>WhereAU</Title>
        <Logo src="./public/WhereRU.png" alt="WhereAU Logo" />
      </Brand>
      <UserContainer>
        <UserAvatar />
        <Logout onClick={handleLogout}>Logout</Logout>
      </UserContainer>
    </StyledHeader>
  );
}

export default Header;
