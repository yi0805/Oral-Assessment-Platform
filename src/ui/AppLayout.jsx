import { Outlet } from "react-router";
import styled from "styled-components";

import Header from "./Header";
import Sidebar from "./Sidebar";

const StyleAppLayout = styled.div`
  display: grid;
  grid-template-columns: 16rem 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas: "header header" "sidebar main";
  height: 100vh;
  background: #2574ce21;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
    grid-template-areas: "header" "sidebar" "main";
  }
`;

const Main = styled.main`
  grid-area: main;
  overflow: auto;
  padding: var(--space-3xl);
  min-width: 0;
`;

function AppLayout() {
  return (
    <StyleAppLayout>
      <Header />
      <Sidebar />

      <Main>
        <Outlet />
      </Main>
    </StyleAppLayout>
  );
}

export default AppLayout;
