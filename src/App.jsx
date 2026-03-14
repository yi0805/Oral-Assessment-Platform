import styled from "styled-components";

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
    </>
  );
}

export default App;
