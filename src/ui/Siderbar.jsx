import styled from "styled-components";

const StyledSidebar = styled.div`
  background-color: rebeccapurple;
  padding: 1rem;
  height: 100%;
  grid-area: sidebar;
`;

function Siderbar() {
  return <StyledSidebar>SideBar Here</StyledSidebar>;
}

export default Siderbar;
