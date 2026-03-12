<script lang="ts">
  import '../app.css';
  import { authStore, isAdmin } from '$lib/stores';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';

  interface Props {
    children: import('svelte').Snippet;
    data: { pathname: string };
  }

  let { children, data }: Props = $props();

  const publicRoutes = ['/login'];

  onMount(() => {
    const unsubscribe = authStore.subscribe(($auth) => {
      const path = $page.url.pathname;
      if (!$auth.token && !publicRoutes.includes(path)) {
        goto('/login');
      }
    });
    return unsubscribe;
  });

  function logout() {
    authStore.logout();
    goto('/login');
  }

  let mobileMenuOpen = $state(false);
</script>

{#if $page.url.pathname === '/login'}
  {@render children()}
{:else}
  <div class="min-h-screen bg-gray-50">
    <!-- Navbar -->
    <nav class="bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center justify-between">
          <div class="flex items-center gap-8">
            <a href="/" class="flex items-center gap-2">
              <span class="text-xl font-bold text-blue-700">IB-Oxford</span>
              <span class="text-sm text-gray-400 hidden sm:block">Dashboard</span>
            </a>
            <div class="hidden md:flex items-center gap-1">
              <a
                href="/"
                class="px-3 py-2 rounded-md text-sm font-medium transition-colors {$page.url.pathname === '/' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'}"
              >
                Home
              </a>
              <a
                href="/query"
                class="px-3 py-2 rounded-md text-sm font-medium transition-colors {$page.url.pathname.startsWith('/query') ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'}"
              >
                Query Builder
              </a>
              {#if $isAdmin}
                <a
                  href="/admin"
                  class="px-3 py-2 rounded-md text-sm font-medium transition-colors {$page.url.pathname.startsWith('/admin') ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'}"
                >
                  Admin
                </a>
              {/if}
            </div>
          </div>

          <div class="flex items-center gap-3">
            {#if $authStore.user}
              <div class="hidden md:flex items-center gap-2">
                <span class="text-sm text-gray-500">
                  {$authStore.user.username}
                </span>
                {#if $authStore.user.is_admin}
                  <span class="badge badge-blue">admin</span>
                {/if}
              </div>
            {/if}
            <button class="btn-secondary btn-sm" onclick={logout}>Sign out</button>
            <button
              class="md:hidden p-2 rounded-md text-gray-500 hover:bg-gray-100"
              onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
              aria-label="Menu"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      {#if mobileMenuOpen}
        <div class="md:hidden border-t border-gray-200 px-4 py-3 space-y-1">
          <a href="/" class="block px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100" onclick={() => (mobileMenuOpen = false)}>Home</a>
          <a href="/query" class="block px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100" onclick={() => (mobileMenuOpen = false)}>Query Builder</a>
          {#if $isAdmin}
            <a href="/admin" class="block px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100" onclick={() => (mobileMenuOpen = false)}>Admin</a>
          {/if}
          {#if $authStore.user}
            <div class="px-3 py-2 text-sm text-gray-500">{$authStore.user.username}</div>
          {/if}
        </div>
      {/if}
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {@render children()}
    </main>
  </div>
{/if}
