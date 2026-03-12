import { h as head, d as attr } from "../../../chunks/index2.js";
import "@sveltejs/kit/internal";
import "../../../chunks/exports.js";
import "../../../chunks/utils.js";
import "@sveltejs/kit/internal/server";
import "../../../chunks/root.js";
import "../../../chunks/state.svelte.js";
import "../../../chunks/stores.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let username = "";
    let password = "";
    let loading = false;
    head("1x05zx6", $$renderer2, ($$renderer3) => {
      $$renderer3.title(($$renderer4) => {
        $$renderer4.push(`<title>Sign In — IB-Oxford Dashboard</title>`);
      });
    });
    $$renderer2.push(`<div class="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center px-4"><div class="w-full max-w-md"><div class="text-center mb-8"><h1 class="text-3xl font-bold text-white">IB-Oxford</h1> <p class="text-blue-200 mt-1">Longitudinal Data Dashboard</p></div> <div class="bg-white rounded-2xl shadow-xl p-8"><h2 class="text-xl font-semibold text-gray-800 mb-6">Sign In</h2> <form class="space-y-5"><div><label class="label" for="username">Username</label> <input id="username" type="text" class="input"${attr("value", username)} autocomplete="username" required=""${attr("disabled", loading, true)} placeholder="your.username"/></div> <div><label class="label" for="password">Password</label> <input id="password" type="password" class="input"${attr("value", password)} autocomplete="current-password" required=""${attr("disabled", loading, true)} placeholder="••••••••"/></div> `);
    {
      $$renderer2.push("<!--[-1-->");
    }
    $$renderer2.push(`<!--]--> <button type="submit" class="btn-primary w-full justify-center py-2.5"${attr("disabled", loading, true)}>`);
    {
      $$renderer2.push("<!--[-1-->");
      $$renderer2.push(`Sign In`);
    }
    $$renderer2.push(`<!--]--></button></form></div> <p class="text-center text-blue-200 text-xs mt-6">IB-Oxford Wellbeing Research · Read-only access</p></div></div>`);
  });
}
export {
  _page as default
};
