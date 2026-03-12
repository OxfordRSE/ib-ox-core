// @ts-nocheck
import type { LayoutLoad } from './$types';

export const ssr = false;

export const load = ({ url }: Parameters<LayoutLoad>[0]) => {
  return { pathname: url.pathname };
};
