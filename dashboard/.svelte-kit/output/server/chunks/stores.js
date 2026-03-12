import { d as derived, w as writable } from "./index.js";
function createAuthStore() {
  const initial = typeof localStorage !== "undefined" ? {
    token: localStorage.getItem("ib_ox_token"),
    user: (() => {
      try {
        const raw = localStorage.getItem("ib_ox_user");
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    })()
  } : { token: null, user: null };
  const { subscribe, set, update } = writable(initial);
  return {
    subscribe,
    login(token, user) {
      if (typeof localStorage !== "undefined") {
        localStorage.setItem("ib_ox_token", token);
        localStorage.setItem("ib_ox_user", JSON.stringify(user));
      }
      set({ token, user });
    },
    logout() {
      if (typeof localStorage !== "undefined") {
        localStorage.removeItem("ib_ox_token");
        localStorage.removeItem("ib_ox_user");
      }
      set({ token: null, user: null });
    },
    updateUser(user) {
      if (typeof localStorage !== "undefined") {
        localStorage.setItem("ib_ox_user", JSON.stringify(user));
      }
      update((s) => ({ ...s, user }));
    }
  };
}
const authStore = createAuthStore();
derived(authStore, ($a) => !!$a.token);
const isAdmin = derived(authStore, ($a) => !!$a.user?.is_admin);
export {
  authStore as a,
  isAdmin as i
};
