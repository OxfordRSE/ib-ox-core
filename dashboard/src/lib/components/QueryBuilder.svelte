<script lang="ts">
  import { authStore } from '$lib/stores';
  import {
    queryFrequency,
    queryMeans,
    ApiError
  } from '$lib/api';
  import type { FrequencyResult, MeansResult, QueryFilter } from '$lib/api';
  import ChartCard from './ChartCard.svelte';
  import { frequencyToChartData, meansToChartData } from '$lib/chartUtils';

  // Whitelist from API — keep in sync with api/src/ib_ox_api/query.py
  const CATEGORICAL_COLS = [
    'school', 'yearGroup', 'class', 'sex', 'ethnicity', 'wave', 'd_city', 'd_country'
  ];
  const NUMERIC_COLS = [
    'phq9_1', 'phq9_2', 'phq9_3', 'phq9_4', 'phq9_5',
    'phq9_6', 'phq9_7', 'phq9_8', 'phq9_9', 'd_age'
  ];

  interface Props {
    columns: string[];
  }

  let { columns }: Props = $props();

  // Available columns (intersection with whitelists)
  const availableCategorical = $derived(
    CATEGORICAL_COLS.filter((c) => columns.includes(c))
  );
  const availableNumeric = $derived(NUMERIC_COLS.filter((c) => columns.includes(c)));

  type QueryType = 'frequency' | 'means';
  let queryType = $state<QueryType>('frequency');
  let groupBy = $state<string[]>([]);
  let valueColumns = $state<string[]>([]);
  let valueColumn = $state('');
  let filters = $state<QueryFilter[]>([]);

  let loading = $state(false);
  let error = $state<string | null>(null);
  let freqResult = $state<FrequencyResult | null>(null);
  let meansResult = $state<MeansResult | null>(null);

  function toggleGroupBy(col: string) {
    if (groupBy.includes(col)) {
      groupBy = groupBy.filter((c) => c !== col);
    } else {
      groupBy = [...groupBy, col];
    }
  }

  function toggleValueColumn(col: string) {
    if (valueColumns.includes(col)) {
      valueColumns = valueColumns.filter((c) => c !== col);
    } else {
      valueColumns = [...valueColumns, col];
    }
  }

  function addFilter() {
    filters = [...filters, { column: columns[0] ?? '', op: 'eq', value: '' }];
  }

  function removeFilter(idx: number) {
    filters = filters.filter((_, i) => i !== idx);
  }

  async function runQuery() {
    const token = $authStore.token;
    if (!token) return;
    error = null;
    loading = true;
    freqResult = null;
    meansResult = null;
    try {
      if (queryType === 'frequency') {
        freqResult = await queryFrequency(token, {
          group_by: groupBy,
          filters,
          value_column: valueColumn || undefined
        });
      } else {
        meansResult = await queryMeans(token, {
          group_by: groupBy,
          value_columns: valueColumns,
          filters
        });
      }
    } catch (e: unknown) {
      if (e instanceof ApiError) {
        error = `API error ${e.status}: ${e.message}`;
      } else {
        error = e instanceof Error ? e.message : 'Query failed';
      }
    } finally {
      loading = false;
    }
  }

  const freqChart = $derived(
    freqResult ? frequencyToChartData(freqResult, groupBy) : null
  );
  const meansChart = $derived(
    meansResult ? meansToChartData(meansResult, groupBy) : null
  );
  const isValid = $derived(
    groupBy.length > 0 &&
    (queryType === 'frequency' || valueColumns.length > 0)
  );
</script>

<div class="space-y-6">
  <!-- Query type selector -->
  <div class="card">
    <div class="flex gap-4">
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name="queryType"
          value="frequency"
          bind:group={queryType}
          class="text-blue-600"
        />
        <span class="font-medium">Frequency Table</span>
        <span class="text-xs text-gray-500">(count distinct students)</span>
      </label>
      <label class="flex items-center gap-2 cursor-pointer">
        <input
          type="radio"
          name="queryType"
          value="means"
          bind:group={queryType}
          class="text-blue-600"
        />
        <span class="font-medium">Means Table</span>
        <span class="text-xs text-gray-500">(average questionnaire scores)</span>
      </label>
    </div>
  </div>

  <!-- Group by -->
  <div class="card space-y-3">
    <h3 class="font-semibold text-gray-700">Group By</h3>
    <p class="text-xs text-gray-500">Select one or more categorical columns.</p>
    <div class="flex flex-wrap gap-2">
      {#each availableCategorical as col}
        <button
          class="px-3 py-1.5 rounded-full text-sm border transition-colors
            {groupBy.includes(col)
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'}"
          onclick={() => toggleGroupBy(col)}
        >
          {col}
        </button>
      {/each}
      {#if availableCategorical.length === 0}
        <p class="text-sm text-gray-400 italic">No categorical columns available.</p>
      {/if}
    </div>
  </div>

  <!-- Value columns (means) or value_column (frequency pivot) -->
  {#if queryType === 'means'}
    <div class="card space-y-3">
      <h3 class="font-semibold text-gray-700">Value Columns</h3>
      <p class="text-xs text-gray-500">Select columns to average.</p>
      <div class="flex flex-wrap gap-2">
        {#each availableNumeric as col}
          <button
            class="px-3 py-1.5 rounded-full text-sm border transition-colors
              {valueColumns.includes(col)
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white text-gray-700 border-gray-300 hover:border-green-400'}"
            onclick={() => toggleValueColumn(col)}
          >
            {col}
          </button>
        {/each}
        {#if availableNumeric.length === 0}
          <p class="text-sm text-gray-400 italic">No numeric columns available.</p>
        {/if}
      </div>
    </div>
  {:else}
    <div class="card space-y-3">
      <h3 class="font-semibold text-gray-700">Pivot Column <span class="text-gray-400 font-normal">(optional)</span></h3>
      <p class="text-xs text-gray-500">
        Cross-tabulate by this column (creates one column per unique value).
      </p>
      <select class="input max-w-xs" bind:value={valueColumn}>
        <option value="">— None (simple count) —</option>
        {#each availableCategorical as col}
          <option value={col}>{col}</option>
        {/each}
      </select>
    </div>
  {/if}

  <!-- Filters -->
  <div class="card space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="font-semibold text-gray-700">Filters <span class="text-gray-400 font-normal">(optional)</span></h3>
      <button class="btn-secondary btn-sm" onclick={addFilter}>+ Add Filter</button>
    </div>

    {#if filters.length === 0}
      <p class="text-sm text-gray-400 italic">No filters applied.</p>
    {:else}
      <div class="space-y-2">
        {#each filters as filter, fi}
          <div class="flex items-center gap-2">
            <select class="input flex-1" bind:value={filter.column}>
              {#each columns as col}
                <option value={col}>{col}</option>
              {/each}
            </select>
            <select class="input w-24" bind:value={filter.op}>
              <option value="eq">=</option>
              <option value="ne">≠</option>
              <option value="in">in</option>
              <option value="gt">&gt;</option>
              <option value="lt">&lt;</option>
              <option value="gte">≥</option>
              <option value="lte">≤</option>
            </select>
            <input
              type="text"
              class="input flex-1"
              bind:value={filter.value as string}
              placeholder="value"
            />
            <button
              class="text-red-400 hover:text-red-600 p-1"
              onclick={() => removeFilter(fi)}
              aria-label="Remove filter"
            >
              ×
            </button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Submit -->
  <div class="flex items-center gap-3">
    <button
      class="btn-primary"
      onclick={runQuery}
      disabled={!isValid || loading}
    >
      {#if loading}
        <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg>
        Running…
      {:else}
        Run Query
      {/if}
    </button>
    {#if !isValid}
      <p class="text-sm text-gray-400">
        {groupBy.length === 0
          ? 'Select at least one Group By column.'
          : 'Select at least one Value Column.'}
      </p>
    {/if}
  </div>

  <!-- Error -->
  {#if error}
    <div class="card bg-red-50 border-red-200 text-red-700 text-sm">{error}</div>
  {/if}

  <!-- Results -->
  {#if freqResult && freqChart}
    <ChartCard
      title="Frequency Query Result"
      type="bar"
      data={freqChart.data}
      options={freqChart.options}
      csv={freqResult.csv}
      suppressions={freqResult.suppressions}
      filename="frequency-result"
    />
  {/if}

  {#if meansResult && meansChart}
    <ChartCard
      title="Means Query Result"
      type="bar"
      data={meansChart.data}
      options={meansChart.options}
      csv={meansResult.csv}
      suppressions={meansResult.suppressions}
      filename="means-result"
    />
  {/if}
</div>
