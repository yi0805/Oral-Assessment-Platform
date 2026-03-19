import { Outlet } from "react-router";
import styled from "styled-components";

import Header from "./Header";
import Siderbar from "./Siderbar";

const StyleAppLayout = styled.div`
  display: grid;
  grid-template-columns: 16rem 1fr;
  grid-template-rows: 4.8rem 1fr;
  grid-template-areas: "header header" "sidebar main";
  height: 100vh;
  background: var(--color-primary-tint);
`;

const Main = styled.main`
  grid-area: main;
  overflow: auto;
  padding: var(--space-3xl);
`;

const Container = styled.div`
  min-height: 100%;
`;

function AppLayout() {
  return (
    <StyleAppLayout>
      <Header />
      <Siderbar />

      <Main>
        <Container>
          <Outlet />
        </Container>
      </Main>
    </StyleAppLayout>
  );
}

export default AppLayout;
