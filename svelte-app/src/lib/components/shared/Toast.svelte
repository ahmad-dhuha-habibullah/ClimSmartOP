<script>
	import { toasts } from '$lib/stores/toast.js';

	function icon(type) {
		if (type === 'error') return 'ti-alert-circle text-lg text-red-600';
		if (type === 'success') return 'ti-circle-check text-lg text-green-600';
		return 'ti-info-circle text-lg text-blue-600';
	}

	function colorClass(type) {
		if (type === 'error') return 'border-red-200 text-red-800 bg-red-50';
		if (type === 'success') return 'border-green-200 text-green-800 bg-green-50';
		return 'border-blue-200 text-blue-800 bg-blue-50';
	}
</script>

<div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
	{#each $toasts as toast (toast.id)}
		<div
			class="px-4 py-3 rounded-xl shadow-lg border text-sm font-semibold pointer-events-auto flex items-center gap-2 bg-white {colorClass(toast.type)}"
			style="animation: fadeIn 0.3s ease-in-out forwards"
		>
			<i class="ti {icon(toast.type)}"></i>
			<span>{toast.message}</span>
		</div>
	{/each}
</div>
