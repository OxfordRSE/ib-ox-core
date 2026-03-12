<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore, isAdmin } from '$lib/stores';
  import { listUsers, createUser, updateUser, deleteUser, ApiError } from '$lib/api';
  import type { User, UserCreate, UserUpdate } from '$lib/api';

  let users = $state<User[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let actionError = $state<string | null>(null);

  // Modal state
  type ModalMode = 'create' | 'edit' | null;
  let modalMode = $state<ModalMode>(null);
  let editingUser = $state<User | null>(null);

  // Form fields
  let formUsername = $state('');
  let formPassword = $state('');
  let formScopeJson = $state('{"filters": {}}');
  let formIsActive = $state(true);
  let formIsAdmin = $state(false);
  let formLoading = $state(false);
  let formError = $state<string | null>(null);

  let deleteTarget = $state<User | null>(null);
  const scopePlaceholder = '{"filters": {"school": ["School A"]}}';

  onMount(async () => {
    if (!$isAdmin) {
      goto('/');
      return;
    }
    await loadUsers();
  });

  async function loadUsers() {
    loading = true;
    error = null;
    try {
      users = await listUsers($authStore.token!);
    } catch (e: unknown) {
      error = e instanceof Error ? e.message : 'Failed to load users';
    } finally {
      loading = false;
    }
  }

  function openCreate() {
    modalMode = 'create';
    editingUser = null;
    formUsername = '';
    formPassword = '';
    formScopeJson = '{"filters": {}}';
    formIsActive = true;
    formIsAdmin = false;
    formError = null;
  }

  function openEdit(user: User) {
    modalMode = 'edit';
    editingUser = user;
    formUsername = user.username;
    formPassword = '';
    formScopeJson = JSON.stringify(user.scope, null, 2);
    formIsActive = user.is_active;
    formIsAdmin = user.is_admin;
    formError = null;
  }

  function closeModal() {
    modalMode = null;
    editingUser = null;
    formError = null;
  }

  async function handleSubmit() {
    formError = null;

    let scope: { filters: Record<string, string[]> };
    try {
      scope = JSON.parse(formScopeJson);
    } catch {
      formError = 'Invalid scope JSON.';
      return;
    }

    formLoading = true;
    try {
      if (modalMode === 'create') {
        const payload: UserCreate = {
          username: formUsername,
          password: formPassword,
          scope,
          is_admin: formIsAdmin
        };
        await createUser($authStore.token!, payload);
      } else if (modalMode === 'edit' && editingUser) {
        const payload: UserUpdate = {
          scope,
          is_active: formIsActive,
          is_admin: formIsAdmin
        };
        if (formPassword) payload.password = formPassword;
        await updateUser($authStore.token!, editingUser.id, payload);
      }
      closeModal();
      await loadUsers();
    } catch (e: unknown) {
      formError = e instanceof Error ? e.message : 'Action failed';
    } finally {
      formLoading = false;
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    deleteLoading = true;
    actionError = null;
    try {
      await deleteUser($authStore.token!, deleteTarget.id);
      deleteTarget = null;
      await loadUsers();
    } catch (e: unknown) {
      actionError = e instanceof Error ? e.message : 'Delete failed';
    } finally {
      deleteLoading = false;
    }
  }
</script>

<svelte:head>
  <title>Admin — IB-Oxford Dashboard</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <div>
      <h1>User Management</h1>
      <p class="text-gray-500 mt-1">Create, edit and delete dashboard users.</p>
    </div>
    <button class="btn-primary" onclick={openCreate}>+ New User</button>
  </div>

  {#if actionError}
    <div class="card bg-red-50 border-red-200 text-red-700 text-sm">{actionError}</div>
  {/if}

  {#if loading}
    <div class="card flex items-center justify-center h-40 text-gray-400">
      <svg class="animate-spin h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
      </svg>
      Loading users…
    </div>
  {:else if error}
    <div class="card bg-red-50 border-red-200 text-red-700">{error}</div>
  {:else}
    <div class="card p-0 overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">ID</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Username</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Status</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Role</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Scope Filters</th>
            <th class="px-6 py-3 text-right font-semibold text-gray-600 uppercase tracking-wider text-xs">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100 bg-white">
          {#each users as user}
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 text-gray-400">{user.id}</td>
              <td class="px-6 py-4 font-medium text-gray-900">{user.username}</td>
              <td class="px-6 py-4">
                {#if user.is_active}
                  <span class="badge badge-green">Active</span>
                {:else}
                  <span class="badge badge-red">Inactive</span>
                {/if}
              </td>
              <td class="px-6 py-4">
                {#if user.is_admin}
                  <span class="badge badge-blue">Admin</span>
                {:else}
                  <span class="badge badge-yellow">User</span>
                {/if}
              </td>
              <td class="px-6 py-4 text-gray-500 text-xs font-mono max-w-xs truncate">
                {JSON.stringify(user.scope.filters) === '{}' ? '— no filters —' : JSON.stringify(user.scope.filters)}
              </td>
              <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button class="btn-secondary btn-sm" onclick={() => openEdit(user)}>Edit</button>
                  {#if user.id !== $authStore.user?.id}
                    <button class="btn-danger btn-sm" onclick={() => (deleteTarget = user)}>Delete</button>
                  {/if}
                </div>
              </td>
            </tr>
          {:else}
            <tr>
              <td colspan="6" class="px-6 py-8 text-center text-gray-400">No users found.</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Create/Edit Modal -->
{#if modalMode}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-screen overflow-y-auto">
      <div class="p-6 border-b border-gray-200">
        <h2 class="text-lg font-semibold">{modalMode === 'create' ? 'Create User' : 'Edit User'}</h2>
      </div>
      <div class="p-6 space-y-4">
        <div>
          <label class="label" for="f-username">Username</label>
          <input
            id="f-username"
            type="text"
            class="input"
            bind:value={formUsername}
            disabled={modalMode === 'edit'}
            placeholder="username"
          />
        </div>

        <div>
          <label class="label" for="f-password">
            Password {modalMode === 'edit' ? '(leave blank to keep current)' : ''}
          </label>
          <input
            id="f-password"
            type="password"
            class="input"
            bind:value={formPassword}
            placeholder={modalMode === 'edit' ? 'New password (optional)' : 'Password'}
            autocomplete="new-password"
          />
        </div>

        <div>
          <label class="label" for="f-scope">Scope (JSON)</label>
          <textarea
            id="f-scope"
            class="input font-mono text-xs h-32 resize-y"
            bind:value={formScopeJson}
            spellcheck="false"
            placeholder={scopePlaceholder}
          ></textarea>
          <p class="text-xs text-gray-400 mt-1">
            Pre-filters applied to all queries for this user. Use <code class="bg-gray-100 px-1 rounded">{'{"filters": {}}'}</code> for no restrictions.
          </p>
        </div>

        <div class="flex items-center gap-6">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" class="rounded border-gray-300" bind:checked={formIsActive} />
            <span class="text-sm text-gray-700">Active</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" class="rounded border-gray-300" bind:checked={formIsAdmin} />
            <span class="text-sm text-gray-700">Admin</span>
          </label>
        </div>

        {#if formError}
          <div class="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {formError}
          </div>
        {/if}
      </div>
      <div class="p-6 border-t border-gray-200 flex justify-end gap-3">
        <button class="btn-secondary" onclick={closeModal} disabled={formLoading}>Cancel</button>
        <button class="btn-primary" onclick={handleSubmit} disabled={formLoading}>
          {formLoading ? 'Saving…' : modalMode === 'create' ? 'Create' : 'Save'}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Delete confirmation -->
{#if deleteTarget}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" role="dialog" aria-modal="true">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 space-y-4">
      <h2 class="text-lg font-semibold text-gray-900">Delete User</h2>
      <p class="text-gray-600">
        Are you sure you want to delete <strong>{deleteTarget.username}</strong>? This cannot be undone.
      </p>
      <div class="flex justify-end gap-3">
        <button class="btn-secondary" onclick={() => (deleteTarget = null)} disabled={deleteLoading}>Cancel</button>
        <button class="btn-danger" onclick={confirmDelete} disabled={deleteLoading}>
          {deleteLoading ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </div>
  </div>
{/if}
