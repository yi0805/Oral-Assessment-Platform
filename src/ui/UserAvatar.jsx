import styled from "styled-components";

const StyledUserAvatar = styled.div`
  display: flex;
  gap: var(--space-m);
  align-items: center;
`;

const Avatar = styled.img`
  width: 2.6rem;
  border-radius: 50%;
  border: 2px solid var(--color-secondary);
`;

const Name = styled.p`
  font-size: var(--font-size-default);
  color: var(--color-dark-2);
  font-weight: 700;
`;

function UserAvatar() {
  const name = "YI";

  return (
    <StyledUserAvatar>
      <Avatar alt="UserAvatar" src="./public/WhereRU.png" />
      <Name>{name}</Name>
    </StyledUserAvatar>
  );
}

export default UserAvatar;
