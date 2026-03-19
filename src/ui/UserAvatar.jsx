import styled from "styled-components";

const StyledUserAvatar = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  align-items: center;
  font-weight: 2rem;
  font-size: 1.4rem;
  justify-content: flex-end;
`;

const Avatar = styled.img`
  display: block;
  width: 3.6rem;
  aspect-ratio: 1;
  object-fit: cover;
  object-position: center;
  border-radius: 50%;
  outline: 2px solid;
`;

function UserAvatar() {
  return (
    <StyledUserAvatar>
      <Avatar />
      <p>User Name</p>
    </StyledUserAvatar>
  );
}

export default UserAvatar;
