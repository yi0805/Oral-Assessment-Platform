import { Outlet } from "react-router";
import styled from "styled-components";

const H1 = styled.h1`
  background-color: red;
  padding: 20px 20px;
  margin-bottom: 30px;
`;

function AppLayout() {
  return (
    <div>
      <H1>AppLayout</H1>
      <Outlet />
    </div>
  );
}

export default AppLayout;
