import styled from "styled-components";
import { NavLink } from "react-router";

const StyledSidebar = styled.div`
  background: var(--color-light);
  border-right: 1px solid var(--color-light-2);
  padding: var(--space-3xl) var(--space-xl);
  height: 100%;
  grid-area: sidebar;
`;

const Nav = styled.nav`
  display: grid;
  gap: var(--space-m);
`;

const Item = styled(NavLink)`
  text-decoration: none;
  color: var(--color-dark-2);
  padding: var(--space-m) var(--space-l);
  border-radius: 12px;

  &.active {
    background: var(--color-secondary-tint);
    color: var(--color-primary);
    font-weight: 700;
  }
`;

function Siderbar() {
  return (
    <StyledSidebar>
      <Nav>
        <Item to="/home">Home</Item>
        <Item to="/profile">Profile</Item>
        <Item to="/settings">Settings</Item>
        <Item to="/help">Help</Item>
      </Nav>
    </StyledSidebar>
  );
}

export default Siderbar;
