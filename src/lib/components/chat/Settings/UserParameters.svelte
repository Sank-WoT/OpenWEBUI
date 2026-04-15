<script lang="ts">
	import { getContext } from 'svelte';
	import { settings } from '$lib/stores';

	const i18n = getContext('i18n');

	export let saveSettings: Function;
</script>

<div id="tab-user_parameters" class="flex flex-col h-full justify-between text-sm mb-6">
	<div class="overflow-y-scroll max-h-[28rem] md:max-h-full space-y-3">
		<div class="text-sm font-medium">{$i18n.t('User Parameters')}</div>
		<p
			class="text-xs leading-relaxed {$settings?.highContrastMode
				? 'text-gray-800 dark:text-gray-100'
				: 'text-gray-500 dark:text-gray-400'}"
		>
			{$i18n.t('User parameters placeholder hint')}
		</p>
	</div>
</div>
