import { Outlet } from "react-router";
import styled from "styled-components";

import Header from "./Header";
import Siderbar from "./Siderbar";

const StyleAppLayout = styled.div`
  display: grid;
  grid-template-columns: 15rem 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas: "header header" "sidebar main";
  height: 100vh;
  background-color: green;
`;

const Main = styled.main`
  grid-area: main;
`;

const Container = styled.div``;

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
