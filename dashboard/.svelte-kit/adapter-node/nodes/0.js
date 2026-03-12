

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const universal = {
  "ssr": false,
  "load": null
};
export const universal_id = "src/routes/+layout.ts";
export const imports = ["_app/immutable/nodes/0.CR0QJ0DG.js","_app/immutable/chunks/DVLnihQ_.js","_app/immutable/chunks/CQk8FP_0.js","_app/immutable/chunks/CvAtS2qi.js","_app/immutable/chunks/DKc8QTNz.js","_app/immutable/chunks/5JMLCGkj.js","_app/immutable/chunks/D9mHL_0X.js","_app/immutable/chunks/CKMcb9xi.js"];
export const stylesheets = ["_app/immutable/assets/0.5_r_mgTw.css"];
export const fonts = [];
