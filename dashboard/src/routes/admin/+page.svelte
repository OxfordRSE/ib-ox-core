<script lang="ts">
  import { goto } from '$app/navigation';
  import { authStore, isAdmin } from '$lib/stores';
  import { listUsers, createUser, updateUser, deleteUser, queryFrequency } from '$lib/api';
  import type { User, UserCreate, UserUpdate } from '$lib/api';

  // Redirect non-admins
  $effect(() => {
    if (!$isAdmin) goto('/');
  });

  // ─── User list via {#await} ──────────────────────────────────────────────────

  let listVersion = $state(0); // increment to trigger a reload

  function loadUsers() {
    return listUsers($authStore.token!);
  }

  // Reactive promise: re-created whenever listVersion changes
  let usersPromise = $derived.by(() => { listVersion; return loadUsers(); });

  function reloadUsers() {
    listVersion += 1;
  }

  // ─── Scope student count ──────────────────────────────────────────────────────

  /**
   * Query the ungrouped frequency endpoint with the user's scope applied as
   * explicit filters (using the admin's token). Returns the student count
   * visible from that user's perspective, or null on error.
   */
  async function loadScopeCount(token: string, user: User): Promise<number | null> {
    const scopeFilters = Object.entries(user.scope.filters).map(([col, vals]) => ({
      column: col,
      op: 'in' as const,
      value: vals
    }));
    try {
      const result = await queryFrequency(token, { group_by: [], filters: scopeFilters });
      const lines = result.csv.trim().split('\n');
      // Expect header "n" on line 0, value on line 1
      if (lines.length < 2 || lines[0].trim() !== 'n') return null;
      const n = Number(lines[1].trim());
      return isNaN(n) ? null : n;
    } catch {
      return null;
    }
  }

  // ─── Modal state ─────────────────────────────────────────────────────────────

  type ModalMode = 'create' | 'edit' | null;
  let modalMode = $state<ModalMode>(null);
  let editingUser = $state<User | null>(null);

  let formUsername = $state('');
  let formPassword = $state('');
  let formScopeJson = $state('{"filters": {}}');
  let formIsActive = $state(true);
  let formIsAdmin = $state(false);
  let formLoading = $state(false);
  let formError = $state<string | null>(null);

  let deleteTarget = $state<User | null>(null);
  let deleteLoading = $state(false);
  let actionError = $state<string | null>(null);

  const scopePlaceholder = '{"filters": {"school": ["School A"]}}';

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
        const payload: UserCreate = { username: formUsername, password: formPassword, scope, is_admin: formIsAdmin };
        await createUser($authStore.token!, payload);
      } else if (modalMode === 'edit' && editingUser) {
        const payload: UserUpdate = { scope, is_active: formIsActive, is_admin: formIsAdmin };
        if (formPassword) payload.password = formPassword;
        await updateUser($authStore.token!, editingUser.id, payload);
      }
      closeModal();
      reloadUsers();
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
      reloadUsers();
    } catch (e: unknown) {
      actionError = e instanceof Error ? e.message : 'Delete failed';
    } finally {
      deleteLoading = false;
    }
  }

  function hasScopeFilters(scope: { filters: Record<string, string[]> }): boolean {
    return Object.keys(scope.filters).length > 0;
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

  {#await usersPromise}
    <div class="card flex items-center justify-center h-40 text-gray-400">
      <svg class="animate-spin h-8 w-8 mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
      </svg>
      Loading users…
    </div>
  {:then users}
    <div class="card p-0 overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">ID</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Username</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Status</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Role</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-600 uppercase tracking-wider text-xs">Scope</th>
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
              <td class="px-6 py-4">
                <!-- Load the student count visible to this user's scope -->
                {#await loadScopeCount($authStore.token!, user)}
                  <span class="text-gray-400 text-xs animate-pulse">counting…</span>
                {:then count}
                  {#if hasScopeFilters(user.scope)}
                    <!-- Show count as a clickable button that opens the filter popover -->
                    <button
                      class="text-xs text-blue-600 hover:underline cursor-pointer"
                      popovertarget="scope-{user.id}"
                      title="Click to see scope filter details"
                    >
                      {count !== null ? `${count} student${count !== 1 ? 's' : ''}` : '—'}
                    </button>
                    <!-- Native HTML popover listing the actual filters -->
                    <div id="scope-{user.id}" popover class="rounded-lg border border-gray-200 shadow-lg bg-white p-3 text-xs max-w-xs z-50">
                      <p class="font-semibold text-gray-700 mb-2">Scope filters for {user.username}</p>
                      <ul class="space-y-1">
                        {#each Object.entries(user.scope.filters) as [col, vals]}
                          <li><span class="font-mono font-medium text-gray-600">{col}:</span> <span class="text-gray-800">{vals.join(', ')}</span></li>
                        {/each}
                      </ul>
                    </div>
                  {:else}
                    <!-- No filters — show total student count, non-clickable -->
                    <span class="text-xs text-gray-500">
                      {count !== null ? `${count} student${count !== 1 ? 's' : ''} (all)` : '— all —'}
                    </span>
                  {/if}
                {:catch}
                  <span class="text-gray-400 text-xs italic">—</span>
                {/await}
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
  {:catch error}
    <div class="card bg-red-50 border-red-200 text-red-700">
      Failed to load users: {error instanceof Error ? error.message : String(error)}
    </div>
  {/await}
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
