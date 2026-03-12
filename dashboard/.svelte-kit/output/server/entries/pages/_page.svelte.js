import { c as ensure_array_like, s as store_get, u as unsubscribe_stores } from "../../chunks/index2.js";
import { a as authStore } from "../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    $$renderer2.push(`<div class="space-y-6"><div><h1>Dashboard</h1> <p class="text-gray-500 mt-1">Overview of IB-Oxford longitudinal questionnaire data.</p></div> `);
    {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<div class="grid grid-cols-1 md:grid-cols-3 gap-6"><!--[-->`);
      const each_array = ensure_array_like([1, 2, 3]);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        each_array[$$index];
        $$renderer2.push(`<div class="card animate-pulse h-64 bg-gray-100"></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--> <div class="card bg-blue-50 border-blue-200"><h2 class="text-blue-900 mb-2">Getting Started</h2> <ul class="text-sm text-blue-800 space-y-1 list-disc list-inside"><li>Use the <a href="/query" class="underline font-medium">Query Builder</a> to create custom frequency and means queries.</li> <li>Charts support "Show Table" for a tabular view and "↓ CSV" to download data.</li> <li>Suppressed cells (small sample sizes) are shown as — to protect privacy.</li> `);
    if (store_get($$store_subs ??= {}, "$authStore", authStore).user?.is_admin) {
      $$renderer2.push("<!--[0-->");
      $$renderer2.push(`<li>As an admin, you can <a href="/admin" class="underline font-medium">manage users</a> and their pre-filters.</li>`);
    } else {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--></ul></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
