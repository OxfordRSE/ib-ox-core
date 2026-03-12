const ssr = false;
const load = ({ url }) => {
  return { pathname: url.pathname };
};
export {
  load,
  ssr
};
