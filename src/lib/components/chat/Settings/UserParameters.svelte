<script lang="ts">
	import { getContext } from 'svelte';
	import { settings } from '$lib/stores';
  
	const i18n = getContext('i18n');
  
	// ✅ Правильное объявление пропсов в Svelte 5
	let { saveSettings }: { saveSettings?: () => Promise<void> } = $props();
  
	// Состояние формы
	let newParamKey = $state('');
	let newParamValue = $state('');
	let isCreating = $state(false);
  
	// Список параметров
	let parameters = $state<Record<string, string>>({});
  
	const startCreate = () => {
	  newParamKey = '';
	  newParamValue = '';
	  isCreating = true;
	};
  
	const handleSave = async () => {
	  const key = newParamKey.trim();
	  const value = newParamValue.trim();
	  
	  if (!key) return;
	  if (key in parameters) {
		console.warn(`Parameter "${key}" already exists`);
		return;
	  }
  
	  // Сохраняем локально
	  parameters[key] = value;
  
	  // Синхронизация с глобальным store (если есть)
	  if (settings?.userParameters) {
		settings.userParameters = { ...settings.userParameters, [key]: value };
	  }
  
	  // Вызов внешнего колбэка
	  if (typeof saveSettings === 'function') {
		await saveSettings();
	  }
  
	  // После сохранения: скрываем форму, оставляем только ключ в списке
	  isCreating = false;
	  newParamKey = '';
	  newParamValue = '';
	};
  
	const handleDelete = (key: string) => {
	  const { [key]: _, ...rest } = parameters;
	  parameters = rest;
	  
	  if (settings?.userParameters) {
		settings.userParameters = rest;
	  }
	  saveSettings?.();
	};
  
	const handleCancel = () => {
	  isCreating = false;
	  newParamKey = '';
	  newParamValue = '';
	};
  </script>
  
  <div id="tab-user_parameters" class="flex flex-col h-full justify-between text-sm mb-6">
	<div class="overflow-y-scroll max-h-[28rem] md:max-h-full space-y-3">
	  
	  <!-- Заголовок -->
	  <div class="text-sm font-medium">{$i18n.t('User Parameters')}</div>
	  <p class="text-xs leading-relaxed {$settings?.highContrastMode 
		? 'text-gray-800 dark:text-gray-100' 
		: 'text-gray-500 dark:text-gray-400'}">
		{$i18n.t('User parameters placeholder hint')}
	  </p>
  
	  <!-- Список сохранённых параметров (отображаем только ключи) -->
	  {#if Object.keys(parameters).length > 0}
		<div class="space-y-2 mt-3">
		  {#each Object.entries(parameters) as [key, value]}
			<div class="flex items-center justify-between p-2 rounded-lg 
						bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
			  <!-- Показываем ТОЛЬКО ключ -->
			  <span class="font-mono text-sm text-gray-800 dark:text-gray-200">{key}</span>
			  
			  <button
				on:click={() => handleDelete(key)}
				class="p-1 text-gray-400 hover:text-red-500 transition-colors"
				title="{$i18n.t('Delete')}"
			  >
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
						d="M6 18L18 6M6 6l12 12"/>
				</svg>
			  </button>
			</div>
		  {/each}
		</div>
	  {/if}
  
	  <!-- Форма создания -->
	  {#if isCreating}
		<div class="mt-3 p-3 rounded-lg border border-blue-300 dark:border-blue-700 
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
			  {$i18n.t('Save')}
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
		  on:click={startCreate}
		  class="mt-3 flex items-center gap-1.5 text-xs font-medium 
				 text-blue-600 dark:text-blue-400 
				 hover:text-blue-700 dark:hover:text-blue-300
				 transition-colors"
		>
		  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
		  </svg>
		  {$i18n.t('Add parameter')}
		</button>
	  {/if}
  
	</div>
  </div>
