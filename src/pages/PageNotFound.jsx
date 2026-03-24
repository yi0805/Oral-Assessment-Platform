import StandaloneLayout from "../ui/StandaloneLayout";
import BaseCard from "../ui/BaseCard";
import Heading from "../ui/Heading";
import BodyText from "../ui/BodyText";
import ActionsContainer from "../ui/ActionsContainer";
import ButtonLink from "../ui/ButtonLink";

function PageNotFound() {
  return (
    <StandaloneLayout>
      <BaseCard $variant="notFound">
        <Heading>404 - Page Not Found</Heading>
        <BodyText>
          The page you&apos;re looking for doesn&apos;t exist. Use one of the
          options below to continue.
        </BodyText>

        <ActionsContainer>
          <ButtonLink to="/home" $variant="primary">
            Go to Home
          </ButtonLink>
          <ButtonLink to="/login" $variant="secondary">
            Go to Login
          </ButtonLink>
        </ActionsContainer>
      </BaseCard>
    </StandaloneLayout>
  );
}

export default PageNotFound;
