<script>
	let { sqlReady = false } = $props();
	let imgError = $state(false);
</script>

<div
	class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-4 bg-white p-5 rounded-2xl border border-gray-200 shadow-sm"
>
	<div class="flex flex-col sm:flex-row items-start sm:items-center gap-4 sm:gap-5">
		{#if !imgError}
			<img
				src="/clim-smart-op-logo.png"
				alt="ClimSmart-OP"
				class="h-12 sm:h-14 object-contain shrink-0"
				onerror={() => (imgError = true)}
			/>
		{:else}
			<h1 class="text-2xl font-extrabold text-gray-900 tracking-tight">ClimSmart-OP Platform</h1>
		{/if}
		<p
			class="text-sm sm:text-base text-gray-800 font-bold sm:border-l-2 sm:border-gray-200 sm:pl-5 leading-snug max-w-md"
		>
			Integrated Climate-Driven Platform for Adaptive Oil Palm Management
		</p>
	</div>
	<div
		class="flex flex-wrap gap-3 text-xs font-semibold text-gray-500 uppercase tracking-wider bg-gray-50 px-4 py-2 rounded-lg border border-gray-100 shrink-0"
	>
		<div class="flex items-center gap-1.5">
			<span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span> APIs Live
		</div>
		<div class="flex items-center gap-1.5">
			<span class="w-2 h-2 rounded-full {sqlReady ? 'bg-blue-500' : 'bg-amber-500 animate-pulse'}"></span>
			Local DB Engine
		</div>
	</div>
</div>
