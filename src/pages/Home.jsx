import styled from "styled-components";

const Styledhome = styled.section`
  padding: var(--space-4xl);
`;

function Home() {
  return (
    <Styledhome>
      <h1>Home Content</h1>
    </Styledhome>
  );
}

export default Home;
