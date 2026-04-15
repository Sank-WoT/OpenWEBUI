<!-- src/lib/components/chat/Settings/UserParameters.svelte -->
<script lang="ts">
	import { getContext } from 'svelte';
	import { settings } from '$lib/stores';
  
	const i18n = getContext('i18n');
	let { saveSettings }: { saveSettings?: () => Promise<void> } = $props();
  
	// Состояние формы
	let newParamKey = $state('');
	let newParamValue = $state('');
	let isCreating = $state(false);
	
	// 🔑 Ключи из Vault (отображаем только их)
	let vaultKeys = $state<string[]>([]);
	let vaultLoading = $state(false);
	let vaultError = $state<string | null>(null);
	
	// Путь в Vault (можно вынести в настройки пользователя)
	const VAULT_PATH = '40serobabovas@region.cbr.ru';
  
	// Загрузка ключей при монтировании
	$effect(() => {
	  loadVaultKeys();
	});
  
	const loadVaultKeys = async () => {
	  vaultLoading = true;
	  vaultError = null;
	  
	  try {
		const encodedPath = encodeURIComponent(VAULT_PATH);
		const response = await fetch(`/api/v1/vault/keys/${encodedPath}`, {
		  credentials: 'include' // 🔑 отправляет session cookie
		});
		
		if (!response.ok) {
		  const err = await response.json().catch(() => ({}));
		  throw new Error(err.detail || `HTTP ${response.status}`);
		}
		
		const data = await response.json();
		vaultKeys = data.keys || [];
		
	  } catch (err: any) {
		console.error('Failed to load Vault keys:', err);
		vaultError = err.message || 'Failed to connect to Vault';
		vaultKeys = [];
	  } finally {
		vaultLoading = false;
	  }
	};
  
	// ✅ Сохранение параметра в Vault
	const handleSave = async () => {
	  const key = newParamKey.trim();
	  const value = newParamValue.trim();
	  
	  if (!key) return;
  
	  try {
		const encodedPath = encodeURIComponent(VAULT_PATH);
		const response = await fetch(`/api/v1/vault/data/${encodedPath}`, {
		  method: 'PUT',
		  headers: { 'Content-Type': 'application/json' },
		  credentials: 'include',
		  body: JSON.stringify({ key, value })
		});
		
		if (!response.ok) {
		  const err = await response.json().catch(() => ({}));
		  throw new Error(err.detail || `HTTP ${response.status}`);
		}
		
		// ✅ Успех: обновляем список ключей и очищаем форму
		await loadVaultKeys(); // перезагружаем список
		isCreating = false;
		newParamKey = '';
		newParamValue = '';
		
		// Опционально: вызываем внешний saveSettings для синхронизации
		await saveSettings?.();
		
	  } catch (err: any) {
		console.error('Failed to save to Vault:', err);
		alert(`Error: ${err.message}`);
		// Не скрываем форму при ошибке — пользователь может исправить
	  }
	};
  
	// ✅ Удаление параметра из Vault
	const handleDelete = async (key: string) => {
	  if (!confirm(`Delete parameter "${key}" from Vault?`)) return;
	  
	  try {
		const encodedPath = encodeURIComponent(VAULT_PATH);
		const response = await fetch(
		  `/api/v1/vault/data/${encodedPath}?key=${encodeURIComponent(key)}`, 
		  {
			method: 'DELETE',
			credentials: 'include'
		  }
		);
		
		if (!response.ok) {
		  const err = await response.json().catch(() => ({}));
		  throw new Error(err.detail || `HTTP ${response.status}`);
		}
		
		// Обновляем список после удаления
		await loadVaultKeys();
		await saveSettings?.();
		
	  } catch (err: any) {
		console.error('Failed to delete from Vault:', err);
		alert(`Error: ${err.message}`);
	  }
	};
  
	const handleCancel = () => {
	  isCreating = false;
	  newParamKey = '';
	  newParamValue = '';
	};
  </script>
  
  <div id="tab-user_parameters" class="flex flex-col h-full justify-between text-sm mb-6">
	<div class="overflow-y-scroll max-h-[28rem] md:max-h-full space-y-4">
	  
	  <!-- === VAULT KEYS SECTION === -->
	  <div class="space-y-2">
		<div class="flex items-center justify-between">
		  <div class="text-sm font-medium">{$i18n.t('Vault Parameters')}</div>
		  <button
			on:click={loadVaultKeys}
			disabled={vaultLoading}
			class="p-1 text-gray-400 hover:text-blue-500 disabled:opacity-50 transition-colors"
			title="{$i18n.t('Refresh')}"
		  >
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" class:animate-spin={vaultLoading}>
			  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
			</svg>
		  </button>
		</div>
		
		<p class="text-xs {$settings?.highContrastMode ? 'text-gray-800 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}">
		  {$i18n.t('Stored in Vault:')} <code class="bg-gray-100 dark:bg-gray-800 px-1 rounded">{VAULT_PATH}</code>
		</p>
  
		{#if vaultLoading}
		  <div class="flex items-center gap-2 text-xs text-gray-500">
			<span class="animate-pulse">⬤</span> {$i18n.t('Loading...')}
		  </div>
		{:else if vaultError}
		  <div class="text-xs text-red-500 bg-red-50 dark:bg-red-900/20 p-2 rounded">
			⚠️ {vaultError}
		  </div>
		{:else if vaultKeys.length > 0}
		  <div class="space-y-1">
			{#each vaultKeys as key}
			  <!-- ✅ Отображаем ТОЛЬКО ключ (значение скрыто) -->
			  <div class="flex items-center justify-between p-2 rounded-lg 
						  bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
				<span class="font-mono text-sm text-gray-800 dark:text-gray-200">{key}</span>
				<div class="flex items-center gap-1">
				  <span class="text-xs text-gray-400">🔐</span>
				  <button
					on:click={() => handleDelete(key)}
					class="p-1 text-gray-400 hover:text-red-500 transition-colors"
					title="{$i18n.t('Delete')}"
				  >
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				  </button>
				</div>
			  </div>
			{/each}
		  </div>
		{:else}
		  <div class="text-xs text-gray-400 italic">{$i18n.t('No parameters in Vault')}</div>
		{/if}
	  </div>
  
	  <hr class="border-gray-200 dark:border-gray-700" />
  
	  <!-- === FORM FOR ADDING NEW PARAMETER === -->
	  {#if isCreating}
		<div class="p-3 rounded-lg border border-blue-300 dark:border-blue-700 
					bg-blue-50 dark:bg-blue-900/20 space-y-2">
		  
		  <div class="flex items-center gap-2">
			<label class="text-xs font-medium w-12 shrink-0">{$i18n.t('Key')}</label>
			<input
			  type="text"
			  bind:value={newParamKey}
			  placeholder="parameter_name"
			  class="flex-1 px-2.5 py-1.5 text-sm rounded-md border
					 bg-white dark:bg-gray-700
					 border-gray-300 dark:border-gray-600
					 focus:ring-2 focus:ring-blue-500 focus:outline-none"
			/>
		  </div>
  
		  <div class="flex items-center gap-2">
			<label class="text-xs font-medium w-12 shrink-0">{$i18n.t('Value')}</label>
			<input
			  type="text"
			  bind:value={newParamValue}
			  placeholder="parameter_value"
			  class="flex-1 px-2.5 py-1.5 text-sm rounded-md border
					 bg-white dark:bg-gray-700
					 border-gray-300 dark:border-gray-600
					 focus:ring-2 focus:ring-blue-500 focus:outline-none"
			/>
		  </div>
  
		  <div class="flex gap-2 pt-1">
			<button
			  on:click={handleSave}
			  disabled={!newParamKey.trim()}
			  class="px-3 py-1.5 text-xs font-medium text-white 
					 bg-blue-600 hover:bg-blue-700 
					 disabled:bg-gray-400 disabled:cursor-not-allowed
					 rounded-md transition-colors"
			>
			  {$i18n.t('Save to Vault')}
			</button>
			<button
			  on:click={handleCancel}
			  class="px-3 py-1.5 text-xs font-medium 
					 text-gray-700 dark:text-gray-200
					 bg-gray-200 dark:bg-gray-700 
					 hover:bg-gray-300 dark:hover:bg-gray-600
					 rounded-md transition-colors"
			>
			  {$i18n.t('Cancel')}
			</button>
		  </div>
		</div>
	  {:else}
		<button
		  on:click={() => { isCreating = true; newParamKey = ''; newParamValue = ''; }}
		  class="mt-2 flex items-center gap-1.5 text-xs font-medium 
				 text-blue-600 dark:text-blue-400 
				 hover:text-blue-700 dark:hover:text-blue-300
				 transition-colors"
		>
		  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
		  </svg>
		  {$i18n.t('Add parameter to Vault')}
		</button>
	  {/if}
  
	</div>
  </div>
