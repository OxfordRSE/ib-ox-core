<script lang="ts">
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores';
  import { login, getMe, ApiError } from '$lib/api';

  let username = $state('');
  let password = $state('');
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = null;
    loading = true;
    try {
      const token = await login(username, password);
      const user = await getMe(token.access_token);
      authStore.login(token.access_token, user);
      goto('/');
    } catch (e: unknown) {
      if (e instanceof ApiError && e.status === 401) {
        error = 'Invalid username or password.';
      } else {
        error = e instanceof Error ? e.message : 'Login failed. Please try again.';
      }
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Sign In — IB-Oxford Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center px-4">
  <div class="w-full max-w-md">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-white">IB-Oxford</h1>
      <p class="text-blue-200 mt-1">Longitudinal Data Dashboard</p>
    </div>

    <div class="bg-white rounded-2xl shadow-xl p-8">
      <h2 class="text-xl font-semibold text-gray-800 mb-6">Sign In</h2>

      <form onsubmit={handleSubmit} class="space-y-5">
        <div>
          <label class="label" for="username">Username</label>
          <input
            id="username"
            type="text"
            class="input"
            bind:value={username}
            autocomplete="username"
            required
            disabled={loading}
            placeholder="your.username"
          />
        </div>

        <div>
          <label class="label" for="password">Password</label>
          <input
            id="password"
            type="password"
            class="input"
            bind:value={password}
            autocomplete="current-password"
            required
            disabled={loading}
            placeholder="••••••••"
          />
        </div>

        {#if error}
          <div class="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {error}
          </div>
        {/if}

        <button
          type="submit"
          class="btn-primary w-full justify-center py-2.5"
          disabled={loading}
        >
          {#if loading}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            Signing in…
          {:else}
            Sign In
          {/if}
        </button>
      </form>
    </div>

    <p class="text-center text-blue-200 text-xs mt-6">
      IB-Oxford Wellbeing Research · Read-only access
    </p>
  </div>
</div>
