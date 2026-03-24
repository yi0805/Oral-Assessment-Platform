import styled from "styled-components";

import InlineGroup from "./InlineGroup";

const Avatar = styled.img`
  width: 100%;
  max-width: 5ch;
  border-radius: 50%;
  border: 2px solid var(--color-secondary);
`;

const Name = styled.p`
  font-size: var(--font-size-default);
  color: var(--color-dark-2);
  font-weight: 700;
`;

function UserAvatar() {
  const name = localStorage.getItem("userName") || "User";
  const picture = localStorage.getItem("userPicture") || "/WhereRU.png";

  return (
    <InlineGroup>
      <Avatar alt="UserAvatar" src={picture} referrerPolicy="no-referrer" />
      <Name>{name}</Name>
    </InlineGroup>
  );
}

export default UserAvatar;
