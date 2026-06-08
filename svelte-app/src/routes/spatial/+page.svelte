<script>
	import { onMount } from 'svelte';
	import Nav from '$lib/components/shared/Nav.svelte';
	import { runDSS, condColor, condBgColor, condLabel } from '$lib/stores/fuzzy.js';

	let blocks = $state([]);
	let selectedBlock = $state(null);
	let mapLayer = $state('score');

	function rnd(a, b) {
		return Math.round(a + (b - a) * Math.random());
	}

	function generateBlock(id) {
		const age = rnd(3, 22);
		const swd = rnd(5, 140);
		const trep = rnd(25, 98);
		const lai = rnd(15, 80);
		const ndvi = rnd(35, 93);
		const gano = Math.min(100, Math.max(0, Math.round((age / 25) * 50 + (Math.random() * 30 - 10))));
		const r = runDSS(swd, trep, lai, ndvi);
		return { id, age, swd, trep, lai, ndvi, gano, score: Math.round(r.crisp), dom: r.dom, firings: r.firings.filter((f) => f.strength > 0.01) };
	}

	function regenerate() {
		blocks = Array.from({ length: 24 }, (_, i) => generateBlock(i + 1));
		selectedBlock = null;
	}

	function getBlockStyle(block) {
		let v;
		if (mapLayer === 'score') v = block.score;
		else if (mapLayer === 'irr') v = 100 - (['Emergency', 'Urgent', 'High', 'Moderate', 'Low', 'None', 'Drain', 'Max Prep', 'Critical'].indexOf(block.dom?.irr || 'None') * 10);
		else v = 100 - block.gano;

		let bgCol, textCol;
		if (v < 25) { bgCol = '#A32D2D'; textCol = '#FCEBEB'; }
		else if (v < 40) { bgCol = '#E24B4A'; textCol = '#FCEBEB'; }
		else if (v < 55) { bgCol = '#EF9F27'; textCol = '#fffbeb'; }
		else if (v < 70) { bgCol = '#C0DD97'; textCol = '#173404'; }
		else { bgCol = '#3B6D11'; textCol = '#EAF3DE'; }
		return { bgCol, textCol, label: mapLayer === 'score' ? block.score : mapLayer === 'gano' ? block.gano + '%' : block.dom?.irr || 'None' };
	}

	onMount(regenerate);
</script>

<svelte:head>
	<title>Spatial & Actions - ClimSmart-OP</title>
</svelte:head>

<Nav activeTab="spatial" />

<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
	<div class="lg:col-span-2 flex flex-col">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-bold text-gray-800">Estate Edge Dashboard</h2>
			<div class="flex items-center gap-3">
				<select bind:value={mapLayer} class="bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-palm-500 px-3 py-1.5 font-medium shadow-sm outline-none">
					<option value="score">DSS Condition Score</option>
					<option value="irr">Irrigation/Action Priority</option>
					<option value="gano">Ganoderma Risk</option>
				</select>
				<button onclick={regenerate} class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-teal-600 rounded-lg hover:bg-teal-700 transition-colors shadow-sm">
					<i class="ti ti-refresh mr-1 text-xs"></i> Sync ApsimX DB
				</button>
			</div>
		</div>
		<div class="card bg-gray-50 p-4 border-dashed mb-4 flex-grow">
			<div class="grid grid-cols-4 sm:grid-cols-6 gap-2 content-start">
				{#each blocks as block (block.id)}
					{@const style = getBlockStyle(block)}
					<button
						onclick={() => (selectedBlock = block)}
						class="rounded-lg p-2 md:p-3 cursor-pointer text-center transition-all hover:scale-105 shadow-sm border border-black/10"
						style="background-color:{style.bgCol}; color:{style.textCol}"
					>
						<div class="font-bold text-xs tracking-tight mb-1">B{String(block.id).padStart(2, '0')}</div>
						<div class="text-[10px] font-mono bg-black/10 rounded px-1 py-0.5 inline-block">{style.label}</div>
					</button>
				{/each}
			</div>
		</div>
		{#if blocks.length > 0}
			{@const avg = Math.round(blocks.reduce((s, b) => s + b.score, 0) / blocks.length)}
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
				<div class="bg-white p-3 rounded-lg border text-center"><div class="text-[10px] uppercase font-bold text-gray-500">Avg Score</div><div class="text-xl font-bold font-mono" style="color:{condColor(avg)}">{avg}</div></div>
				<div class="bg-red-50 p-3 rounded-lg border text-center"><div class="text-[10px] uppercase font-bold text-red-800">Critical</div><div class="text-xl font-bold text-red-700 font-mono">{blocks.filter((b) => b.score < 25).length}</div></div>
				<div class="bg-amber-50 p-3 rounded-lg border text-center"><div class="text-[10px] uppercase font-bold text-amber-800">Stressed</div><div class="text-xl font-bold text-amber-600 font-mono">{blocks.filter((b) => b.score >= 25 && b.score < 40).length}</div></div>
				<div class="bg-palm-50 p-3 rounded-lg border text-center"><div class="text-[10px] uppercase font-bold text-palm-800">Optimal</div><div class="text-xl font-bold text-palm-700 font-mono">{blocks.filter((b) => b.score >= 70).length}</div></div>
			</div>
		{/if}
	</div>
	<div class="flex flex-col h-full">
		<h2 class="text-lg font-bold text-gray-800 mb-4">Block Inspection</h2>
		{#if selectedBlock}
			{@const col = condColor(selectedBlock.score)}
			<div class="card flex flex-col justify-center flex-grow text-left" style="animation: fadeIn 0.2s ease-in-out">
				<div class="flex justify-between items-start mb-4 pb-4 border-b">
					<div><div class="text-[10px] font-bold text-gray-400 uppercase">Inspecting</div><div class="text-xl font-black text-gray-900">Block B{String(selectedBlock.id).padStart(2, '0')}</div></div>
					<div class="text-right"><div class="text-2xl font-bold font-mono" style="color:{col}">{selectedBlock.score}</div><div class="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border" style="color:{col}">{condLabel(selectedBlock.score)}</div></div>
				</div>
				<div class="grid grid-cols-2 gap-x-4 gap-y-2 text-xs mb-4">
					<div class="flex justify-between text-gray-500"><span>ApsimX SWD</span> <span class="font-mono text-gray-900">{selectedBlock.swd} mm</span></div>
					<div class="flex justify-between text-gray-500"><span>Tr/Ep</span> <span class="font-mono text-gray-900">{(selectedBlock.trep / 100).toFixed(2)}</span></div>
					<div class="flex justify-between text-gray-500"><span>LAI</span> <span class="font-mono text-gray-900">{(selectedBlock.lai / 10).toFixed(1)}</span></div>
					<div class="flex justify-between text-gray-500"><span>Gano Risk</span> <span class="font-mono {selectedBlock.gano > 60 ? 'text-red-600 font-bold' : 'text-gray-900'}">{selectedBlock.gano}%</span></div>
				</div>
				<div class="bg-gray-50 rounded-lg p-3 border mb-3" style="border-left:3px solid {col}">
					<div class="text-[10px] font-bold uppercase text-gray-500 mb-1">API Dispatch Command</div>
					<div class="text-xs font-medium text-gray-900">{selectedBlock.dom?.action || 'Status OK. No action dispatched.'}</div>
				</div>
				<div class="mt-auto">
					<div class="text-[10px] font-bold text-gray-400 uppercase mb-1">Fired Rules</div>
					{#each selectedBlock.firings.slice(0, 2) as f}
						<div class="flex justify-between items-center py-1 text-[10px] border-b">
							<span class="truncate pr-2">{f.then}</span>
							<span class="font-mono font-bold" style="color:{condColor(f.score)}">{f.strength.toFixed(2)}</span>
						</div>
					{/each}
					{#if selectedBlock.firings.length === 0}
						<div class="text-[10px] text-gray-500">None active</div>
					{/if}
				</div>
			</div>
		{:else}
			<div class="card flex flex-col justify-center items-center flex-grow text-center text-gray-500 bg-white">
				<i class="ti ti-click text-4xl mb-3 text-gray-300"></i>
				<p class="text-sm">Select a block on the map<br />to view DSS triggers.</p>
			</div>
		{/if}
	</div>
</div>

<div>
	<h3 class="section-title">Automated API Dispatch Log</h3>
	<div class="card-tight overflow-x-auto">
		<table class="data-table min-w-[900px]">
			<thead class="bg-gray-100"><tr><th>Block ID</th><th>Yield Est.</th><th>ApsimX SWD</th><th>DSS Score</th><th>Condition</th><th>Dispatched Action</th><th>Status</th></tr></thead>
			<tbody>
				{#each blocks as b}
					{@const col = condColor(b.score)}
					{@const bg = condBgColor(b.score)}
					<tr>
						<td class="font-bold text-gray-900">B{String(b.id).padStart(2, '0')}</td>
						<td class="font-mono text-xs text-gray-600">{(28 * (b.score / 100)).toFixed(1)} t/ha</td>
						<td class="font-mono text-xs text-gray-600">{b.swd} mm</td>
						<td><span class="font-bold font-mono text-base" style="color:{col}">{b.score}</span></td>
						<td><span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border uppercase" style="background-color:{bg}; color:{col}; border-color:{col}40">{condLabel(b.score)}</span></td>
						<td class="text-xs text-gray-700">{b.dom?.action ? b.dom.action.slice(0, 40) + '…' : '—'}</td>
						<td>{b.score < 40 ? '<span class="text-amber-600 font-bold text-[10px] bg-amber-50 px-2 py-1 rounded border border-amber-200">API SENT</span>' : '<span class="text-gray-400 text-[10px]">STANDBY</span>'}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>
