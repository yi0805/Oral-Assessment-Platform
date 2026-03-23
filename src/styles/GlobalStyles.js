import { createGlobalStyle } from "styled-components";

const GlobalStyle = createGlobalStyle`

/*** Spacing Variables *****/
:root {
  --space-2xs: 3px;
  --space-xs: 6px;
  --space-s: 9px;
  --space-m: 12px;
  --space-l: 15px;
  --space-xl: 18px;
  --space-2xl: 21px;
  --space-3xl: 24px;
  --space-4xl: 48px;
  --space-5xl: 60px;
}

/*** End Spacing Variables *****/
/*** Font Size Variables *****/
:root {
  --font-size-s: 0.89rem;
  --font-size-default: 1rem;
  --font-size-l: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-xxl: 2rem;
}

/*** End Font Size Variables *****/
/*** Border Radius *****/
:root {
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
}

/*** End Border Radius *****/
/*** Shadows *****/
:root {
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 10px 30px rgba(var(--color-primary-rgb), 0.12);
}

/*** End Shadows *****/
/*** Colors *****/
:root {
  /*tints*/
  --color-waitemata: #0c0c48;
  --color-waitemata-rgb: 12, 12, 72;
  --color-waitemata-5-percent-opacity-tint: #f3f3f6;
  --color-waitemata-10-percent-opacity-tint: #e7e7ed;
  --color-waitemata-20-percent-opacity-tint: #ceceda;
  --color-waitemata-30-percent-opacity-tint: #afafc3;
  --color-waitemata-40-percent-opacity-tint: #9e9eb6;
  --color-azure: #1f2bd4; /* Azure */
  --color-azure-rgb: 31, 43, 212; /* Azure */
  --color-azure-10-percent-opacity-tint: #e9eafb;
  --color-azure-20-percent-opacity-tint: #d2d5f6;
  --color-azure-30-percent-opacity-tint: #bcc0f3;
  --color-azure-40-percent-opacity-tint: #a5aaee;
  --color-mahina: #00caef; /* Mahina */
  --color-mahina-rgb: 0, 202, 239; /* Mahina */
  --color-mahina-10-percent-opacity-tint: #e6fafe;
  --color-mahina-20-percent-opacity-tint: #ccf4fc;
  --color-mahina-30-percent-opacity-tint: #b3f0fb;
  --color-mahina-40-percent-opacity-tint: #99eaf9;
  /*uoa blues*/
  --color-primary: var(--color-waitemata, #0c0c48);
  --color-primary-rgb: var(--color-waitemata-rgb, rgb(12, 12, 72));
  --color-primary-tint: var(--color-waitemata-5-percent-opacity-tint, #f3f3f6);
  --color-secondary: var(--color-azure, #1f2bd4);
  --color-secondary-rgb: var(--color-azure-rgb, rgb(31, 43, 212));
  --color-secondary-tint: var(--color-azure-10-percent-opacity-tint, #e9eafb);
  --color-tertiary: var(--color-mahina, #00caef);
  --color-tertiary-rgb: var(--color-mahina-rgb, rgb(0, 202, 239));
  --color-tertiary-tint: var(var(--color-mahina-10-percent-opacity-tint), #e6fafe);
  /*greys*/
  /*light*/
  --color-light: #ffffff;
  --color-light-rgb: 255, 255, 255;
  --color-light-1: #f2f2f2;
  --color-light-1-rgb: 242, 242, 242;
  --color-light-2: #bec3c4;
  /*medium*/
  --color-medium: #d9d9d9;
  --color-medium-rgb: 217, 217, 217;
  /*dark*/
  --color-dark: #000000;
  --color-dark-rgb: 0, 0, 0;
  --color-dark-1: #4a4a4c;
  --color-dark-1-rgb: 74, 74, 76;
  --color-dark-2: #404040;
  --color-dark-2-rgb: 64, 64, 64;
  --color-dark-2-tint: #9f9f9f;
  --color-dark-3: #333333;
  --color-dark-3-rgb: 51, 51, 51;
  --color-dark-3-tint: #747778;
  /* success */
  --color-success: #2ec95c;
  --color-success-rgb: 42, 201, 92;
  /* warning */
  --color-warning: #fdd835;
  --color-warning-rgb: 253, 216, 52;
  /*error*/
  --color-error: #ed0c0c;
  --color-error-rgb: 237, 12, 12;
  --color-error-toast: #f53d3d;
}

/*** End Colors *****/

*,
*::before,
*::after {
  box-sizing: border-box;
  padding: 0;
  margin: 0;
}

body {
  font-family: "Poppins", sans-serif;
  color: var(--color-dark-2);
  font-size: var(--font-size-default);
  line-height: 1.6;
}

input,
button,
select,
textarea {
  font: inherit;
  color: inherit;
}
`;

export default GlobalStyle;
