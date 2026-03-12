import { g as getContext, s as store_get, a as attr_class, b as stringify, e as escape_html, u as unsubscribe_stores } from "../../chunks/index2.js";
import { i as isAdmin, a as authStore } from "../../chunks/stores.js";
import "@sveltejs/kit/internal";
import "../../chunks/exports.js";
import "../../chunks/utils.js";
import "clsx";
import "@sveltejs/kit/internal/server";
import "../../chunks/root.js";
import "../../chunks/state.svelte.js";
const getStores = () => {
  const stores$1 = getContext("__svelte__");
  return {
    /** @type {typeof page} */
    page: {
      subscribe: stores$1.page.subscribe
    },
    /** @type {typeof navigating} */
    navigating: {
      subscribe: stores$1.navigating.subscribe
    },
    /** @type {typeof updated} */
    updated: stores$1.updated
  };
};
const page = {
  subscribe(fn) {
    const store = getStores().page;
    return store.subscribe(fn);
  }
};
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { children, data } = $$props;
    if (store_get($$store_subs ??= {}, "$page", page).url.pathname === "/login") {
      $$renderer2.push("<!--[0-->");
      children($$renderer2);
      $$renderer2.push(`<!---->`);
    } else {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`<div class="min-h-screen bg-gray-50"><nav class="bg-white border-b border-gray-200 shadow-sm"><div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><div class="flex h-16 items-center justify-between"><div class="flex items-center gap-8"><a href="/" class="flex items-center gap-2"><span class="text-xl font-bold text-blue-700">IB-Oxford</span> <span class="text-sm text-gray-400 hidden sm:block">Dashboard</span></a> <div class="hidden md:flex items-center gap-1"><a href="/"${attr_class(`px-3 py-2 rounded-md text-sm font-medium transition-colors ${stringify(store_get($$store_subs ??= {}, "$page", page).url.pathname === "/" ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100")}`)}>Home</a> <a href="/query"${attr_class(`px-3 py-2 rounded-md text-sm font-medium transition-colors ${stringify(store_get($$store_subs ??= {}, "$page", page).url.pathname.startsWith("/query") ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100")}`)}>Query Builder</a> `);
      if (store_get($$store_subs ??= {}, "$isAdmin", isAdmin)) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<a href="/admin"${attr_class(`px-3 py-2 rounded-md text-sm font-medium transition-colors ${stringify(store_get($$store_subs ??= {}, "$page", page).url.pathname.startsWith("/admin") ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:text-gray-900 hover:bg-gray-100")}`)}>Admin</a>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></div></div> <div class="flex items-center gap-3">`);
      if (store_get($$store_subs ??= {}, "$authStore", authStore).user) {
        $$renderer2.push("<!--[0-->");
        $$renderer2.push(`<div class="hidden md:flex items-center gap-2"><span class="text-sm text-gray-500">${escape_html(store_get($$store_subs ??= {}, "$authStore", authStore).user.username)}</span> `);
        if (store_get($$store_subs ??= {}, "$authStore", authStore).user.is_admin) {
          $$renderer2.push("<!--[0-->");
          $$renderer2.push(`<span class="badge badge-blue">admin</span>`);
        } else {
          $$renderer2.push("<!--[-1-->");
        }
        $$renderer2.push(`<!--]--></div>`);
      } else {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--> <button class="btn-secondary btn-sm">Sign out</button> <button class="md:hidden p-2 rounded-md text-gray-500 hover:bg-gray-100" aria-label="Menu"><svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg></button></div></div></div> `);
      {
        $$renderer2.push("<!--[-1-->");
      }
      $$renderer2.push(`<!--]--></nav> <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">`);
      children($$renderer2);
      $$renderer2.push(`<!----></main></div>`);
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _layout as default
};
