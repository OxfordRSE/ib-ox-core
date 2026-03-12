import { h as head } from "../../../chunks/index2.js";
import "../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    head("hdaaj", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Query Builder — IB-Oxford Dashboard</title>`);
      });
    });
    $$renderer2.push(`<div class="space-y-6"><div><h1>Query Builder</h1> <p class="text-gray-500 mt-1">Build custom frequency or means queries over the dataset.</p></div> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="card flex items-center justify-center h-40 text-gray-400"><svg class="animate-spin h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Loading columns…</div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
