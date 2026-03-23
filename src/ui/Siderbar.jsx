import styled from "styled-components";
import { NavLink } from "react-router";

import useRequireAuth from "../hooks/useRequireAuth";

const StyledSidebar = styled.div`
  background: var(--color-light);
  border-right: 1px solid var(--color-light-2);
  padding: var(--space-3xl) var(--space-xl);
  min-height: 100%;
  grid-area: sidebar;

  @media (max-width: 768px) {
    min-height: auto;
    border-right: none;
    border-bottom: 1px solid var(--color-light-2);
    padding: var(--space-m) var(--space-xl);
  }
`;

const Nav = styled.nav`
  display: flex;
  flex-direction: column;
  gap: var(--space-m);

  @media (max-width: 768px) {
    flex-direction: row;
  }
`;

const Item = styled(NavLink)`
  text-decoration: none;
  color: var(--color-dark-2);
  padding: var(--space-m) var(--space-l);
  border-radius: var(--radius-md);

  &:hover:not(.active) {
    background: var(--color-primary-tint);
  }

  &.active {
    background: var(--color-secondary-tint);
    color: var(--color-primary);
    font-weight: 700;
  }
`;

function Siderbar() {
  const role = useRequireAuth();

  return (
    <StyledSidebar>
      <Nav>
        <Item to="/home">Home</Item>
        {role === "student" ? (
          <Item to="/previous-assessment">Previous assessment</Item>
        ) : null}
      </Nav>
    </StyledSidebar>
  );
}

export default Siderbar;
