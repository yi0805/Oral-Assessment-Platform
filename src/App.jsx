import styled from "styled-components";

import Row from "./ui/Row";
import GlobalStyle from "./styles/GlobalStyles";

const H1 = styled.h1`
  font-size: 30px;
  font-weight: 600;
  background-color: yellow;
`;

function App() {
  return (
    <>
      <GlobalStyle />
      <div>
        <H1>Hello world!</H1>
      </div>

      <Row type="vertical">
        <Row type="vertical">
          <p>Item 1</p>

          <p>Item 2</p>
        </Row>

        <Row type="horizontal">
          <p>Item 1</p>
          <p>Item 2</p>
        </Row>
      </Row>
    </>
  );
}

export default App;
