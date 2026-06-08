<script>
	import { onMount } from 'svelte';
	import Nav from '$lib/components/shared/Nav.svelte';
	import { apsimContext } from '$lib/stores/apsim.js';
	import { SWD_MF, TREP_MF, LAI_MF, NDVI_MF, runDSS, condColor, condBgColor, condLabel } from '$lib/stores/fuzzy.js';

	let activeSubTab = $state('thresholds');
	let isMonthly = $state(false);

	let swd = $state(55);
	let trep = $state(60);
	let lai = $state(38);
	let ndvi = $state(60);

	let iSwd = $state(55);
	let iTrep = $state(60);
	let iLai = $state(38);
	let iNdvi = $state(60);

	let result = $derived(runDSS(iSwd, iTrep, iLai, iNdvi, isMonthly));

	onMount(() => {
		const saved = sessionStorage.getItem('dss_inputs');
		const savedMonthly = sessionStorage.getItem('dss_is_monthly');
		if (saved) {
			const inputs = JSON.parse(saved);
			iSwd = inputs.swd;
			iTrep = inputs.trep;
			iLai = inputs.lai;
			iNdvi = inputs.ndvi;
			swd = inputs.swd;
			trep = inputs.trep;
			lai = inputs.lai;
			ndvi = inputs.ndvi;
			activeSubTab = 'inference';
		}
		if (savedMonthly === 'true') isMonthly = true;

		const ctx = $apsimContext;
		if (ctx) isMonthly = ctx.isMonthly;
	});

	function memCard(name, val, color) {
		const bg = val > 0 ? 'bg-white shadow-sm' : 'bg-gray-50/50 opacity-60';
		const topColor = val > 0 ? color : '#e5e7eb';
		return `<div class="rounded-lg p-2 text-center border border-gray-200 border-t-4 ${bg}" style="border-top-color:${topColor}"><div class="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1 truncate">${name}</div><div class="text-sm font-bold ${val > 0 ? 'text-gray-900' : 'text-gray-400'} font-mono">${val.toFixed(2)}</div></div>`;
	}

	function drawMF(canvasId, mfs, value, maxV) {
		const canvas = document.getElementById(canvasId);
		if (!canvas) return;
		const ctx = canvas.getContext('2d');
		const W = canvas.parentElement?.clientWidth || 300;
		const H = 90;
		canvas.width = W;
		canvas.height = H;
		const pad = 8;
		const iW = W - pad * 2;
		const iH = H - pad - 16;
		ctx.clearRect(0, 0, W, H);
		const toX = (v) => pad + (v / maxV) * iW;
		const toY = (m) => pad + iH - m * iH;
		mfs.forEach((mf, idx) => {
			ctx.beginPath();
			ctx.strokeStyle = mf.color;
			ctx.lineWidth = 2.5;
			ctx.lineJoin = 'round';
			for (let i = 0; i <= 100; i++) {
				const v = (i / 100) * maxV;
				const x = toX(v);
				const y = toY(mf.fn(v));
				i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
			}
			ctx.stroke();
			ctx.font = '600 10px "Plus Jakarta Sans", sans-serif';
			ctx.fillStyle = mf.color;
			ctx.fillText(mf.name.slice(0, 6), pad + idx * (iW / (mfs.length - 0.5)), H - 2);
		});
		const vx = toX(value);
		ctx.setLineDash([4, 4]);
		ctx.strokeStyle = '#4b5563';
		ctx.lineWidth = 1.5;
		ctx.beginPath();
		ctx.moveTo(vx, pad);
		ctx.lineTo(vx, pad + iH);
		ctx.stroke();
		ctx.setLineDash([]);
	}

	function updateFuzz() {
		drawMF('c-swd', SWD_MF, swd, 150);
		drawMF('c-trep', TREP_MF, trep, 100);
		drawMF('c-lai', LAI_MF, lai, 85);
		drawMF('c-ndvi', NDVI_MF, ndvi, 95);

		const el = (id) => document.getElementById(id);
		if (el('mem-swd')) el('mem-swd').innerHTML = SWD_MF.map((m) => memCard(m.name, m.fn(swd), m.color)).join('');
		if (el('mem-trep')) el('mem-trep').innerHTML = TREP_MF.map((m) => memCard(m.name, m.fn(trep), m.color)).join('');
		if (el('mem-lai')) el('mem-lai').innerHTML = LAI_MF.map((m) => memCard(m.name, m.fn(lai), m.color)).join('');
		if (el('mem-ndvi')) el('mem-ndvi').innerHTML = NDVI_MF.map((m) => memCard(m.name, m.fn(ndvi), m.color)).join('');
	}

	$effect(() => {
		if (activeSubTab === 'fuzz') {
			setTimeout(updateFuzz, 50);
		}
	});
</script>

<svelte:head>
	<title>DSS Engine - ClimSmart-OP</title>
</svelte:head>

<Nav activeTab="dss" />

<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4">
	<h2 class="text-xl font-bold text-gray-900 mb-2 sm:mb-0"
		>{isMonthly ? 'Seasonal DSS Engine (Long-Term Planning)' : 'DSS Engine'}</h2
	>
	<div class="flex bg-gray-50 p-1.5 rounded-xl border border-gray-200 inline-flex shadow-sm">
		<button class="sub-tab {activeSubTab === 'thresholds' ? 'active' : ''}" onclick={() => (activeSubTab = 'thresholds')}>1. Field Thresholds</button>
		<button class="sub-tab {activeSubTab === 'fuzz' ? 'active' : ''}" onclick={() => (activeSubTab = 'fuzz')}>2. Fuzzification</button>
		<button class="sub-tab {activeSubTab === 'inference' ? 'active' : ''}" onclick={() => (activeSubTab = 'inference')}>3. Fuzzy Inference Simulator</button>
	</div>
</div>

{#if activeSubTab === 'thresholds'}
	<div class="mb-8 card-tight overflow-x-auto">
		<table class="data-table min-w-[800px]">
			<thead class="bg-gray-100">
				<tr><th>ApsimX Variable</th><th>Deficit (Critical)</th><th>Low</th><th>Optimal</th><th>High</th><th>Excess (Risk)</th></tr>
			</thead>
			<tbody>
				<tr><td class="font-medium text-gray-900">Soil water deficit (mm)</td><td><span class="badge-critical">&gt; 80 mm</span></td><td><span class="badge-stressed">50–80 mm</span></td><td><span class="badge-optimal">0–30 mm</span></td><td class="text-gray-400 text-xs font-bold">—</td><td><span class="badge-critical">Saturated</span></td></tr>
				<tr><td class="font-medium text-gray-900">Transpiration ratio (Tr/Ep)</td><td><span class="badge-critical">&lt; 0.40</span></td><td><span class="badge-stressed">0.40–0.65</span></td><td><span class="badge-optimal">0.65–0.95</span></td><td><span class="badge-supra">0.95–1.0</span></td><td><span class="badge-critical">&gt; 1.0</span></td></tr>
				<tr><td class="font-medium text-gray-900">LAI (m²/m²)</td><td><span class="badge-critical">&lt; 2.5</span></td><td><span class="badge-stressed">2.5–4.0</span></td><td><span class="badge-optimal">4.0–6.5</span></td><td><span class="badge-stressed">&gt; 6.5</span></td><td class="text-gray-400 text-xs font-bold">—</td></tr>
				<tr><td class="font-medium text-gray-900">Canopy NDVI</td><td><span class="badge-critical">&lt; 0.52</span></td><td><span class="badge-stressed">0.52–0.65</span></td><td><span class="badge-optimal">0.65–0.82</span></td><td><span class="badge-supra">&gt; 0.82</span></td><td class="text-gray-400 text-xs font-bold">—</td></tr>
			</tbody>
		</table>
	</div>
	<button onclick={() => (activeSubTab = 'fuzz')} class="bg-gray-100 text-gray-700 hover:bg-gray-200 px-4 py-2 rounded-lg text-sm font-semibold transition">Next: View Fuzzification Curves &rarr;</button>
{/if}

{#if activeSubTab === 'fuzz'}
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
		<div class="card flex flex-col">
			<div class="flex justify-between items-end mb-4"><div class="text-sm font-semibold text-gray-700">Soil water deficit (mm)</div><div class="text-lg font-bold text-palm-700 font-mono">{swd} mm</div></div>
			<div class="flex items-center mb-6"><input type="range" min="0" max="150" step="1" bind:value={swd} class="slider" oninput={updateFuzz} /></div>
			<div class="bg-gray-50 rounded-lg border border-gray-200 p-2 mb-4 flex-grow"><canvas id="c-swd" class="w-full" style="height:90px"></canvas></div>
			<div id="mem-swd" class="grid grid-cols-5 gap-2 mt-auto"></div>
		</div>
		<div class="card flex flex-col">
			<div class="flex justify-between items-end mb-4"><div class="text-sm font-semibold text-gray-700">Transpiration ratio Tr/Ep</div><div class="text-lg font-bold text-palm-700 font-mono">{(trep / 100).toFixed(2)}</div></div>
			<div class="flex items-center mb-6"><input type="range" min="0" max="100" step="1" bind:value={trep} class="slider" oninput={updateFuzz} /></div>
			<div class="bg-gray-50 rounded-lg border border-gray-200 p-2 mb-4 flex-grow"><canvas id="c-trep" class="w-full" style="height:90px"></canvas></div>
			<div id="mem-trep" class="grid grid-cols-5 gap-2 mt-auto"></div>
		</div>
		<div class="card flex flex-col">
			<div class="flex justify-between items-end mb-4"><div class="text-sm font-semibold text-gray-700">LAI (m²/m²)</div><div class="text-lg font-bold text-palm-700 font-mono">{(lai / 10).toFixed(1)}</div></div>
			<div class="flex items-center mb-6"><input type="range" min="0" max="85" step="1" bind:value={lai} class="slider" oninput={updateFuzz} /></div>
			<div class="bg-gray-50 rounded-lg border border-gray-200 p-2 mb-4 flex-grow"><canvas id="c-lai" class="w-full" style="height:90px"></canvas></div>
			<div id="mem-lai" class="grid grid-cols-4 gap-2 mt-auto"></div>
		</div>
		<div class="card flex flex-col">
			<div class="flex justify-between items-end mb-4"><div class="text-sm font-semibold text-gray-700">Canopy NDVI</div><div class="text-lg font-bold text-palm-700 font-mono">{(ndvi / 100).toFixed(2)}</div></div>
			<div class="flex items-center mb-6"><input type="range" min="30" max="95" step="1" bind:value={ndvi} class="slider" oninput={updateFuzz} /></div>
			<div class="bg-gray-50 rounded-lg border border-gray-200 p-2 mb-4 flex-grow"><canvas id="c-ndvi" class="w-full" style="height:90px"></canvas></div>
			<div id="mem-ndvi" class="grid grid-cols-4 gap-2 mt-auto"></div>
		</div>
	</div>
	<button onclick={() => (activeSubTab = 'inference')} class="bg-gray-100 text-gray-700 hover:bg-gray-200 px-4 py-2 rounded-lg text-sm font-semibold transition">Next: Fuzzy Inference Engine &rarr;</button>
{/if}

{#if activeSubTab === 'inference'}
	<div class="mb-6 card bg-white border-l-4 border-l-palm-600">
		<h3 class="section-title mb-0">Forecast Aggregated Inputs</h3>
		<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6">
			<div><label for="i-swd" class="block text-xs font-semibold text-gray-500 mb-2">Avg Soil Water Deficit (mm)</label><div class="flex items-center gap-3"><input id="i-swd" type="range" min="0" max="150" step="1" bind:value={iSwd} class="slider flex-grow" /><span class="text-sm font-mono font-bold text-gray-700 w-8 text-right">{iSwd}</span></div></div>
			<div><label for="i-trep" class="block text-xs font-semibold text-gray-500 mb-2">Avg Tr/Ep Ratio</label><div class="flex items-center gap-3"><input id="i-trep" type="range" min="0" max="100" step="1" bind:value={iTrep} class="slider flex-grow" /><span class="text-sm font-mono font-bold text-gray-700 w-10 text-right">{(iTrep / 100).toFixed(2)}</span></div></div>
			<div><label for="i-lai" class="block text-xs font-semibold text-gray-500 mb-2">Avg LAI Output</label><div class="flex items-center gap-3"><input id="i-lai" type="range" min="0" max="85" step="1" bind:value={iLai} class="slider flex-grow" /><span class="text-sm font-mono font-bold text-gray-700 w-8 text-right">{(iLai / 10).toFixed(1)}</span></div></div>
			<div><label for="i-ndvi" class="block text-xs font-semibold text-gray-500 mb-2">Avg NDVI Index</label><div class="flex items-center gap-3"><input id="i-ndvi" type="range" min="30" max="95" step="1" bind:value={iNdvi} class="slider flex-grow" /><span class="text-sm font-mono font-bold text-gray-700 w-10 text-right">{(iNdvi / 100).toFixed(2)}</span></div></div>
		</div>
	</div>

	<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
		<div class="metric-box bg-white border-orange-100" style="box-shadow:0 4px 12px rgba(255,152,0,0.1)"><div class="absolute top-0 left-0 w-full h-1 bg-orange-400"></div><div class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Defuzzified Score</div><div class="text-4xl font-black mt-2 font-mono" style="color:{condColor(result.crisp)}">{Math.round(result.crisp)}</div></div>
		<div class="metric-box bg-white"><div class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Condition</div><div class="text-2xl font-bold mt-3" style="color:{condColor(result.crisp)}">{condLabel(result.crisp)}</div></div>
		<div class="metric-box bg-white"><div class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Action Priority</div><div class="text-xl font-bold mt-3 text-gray-800">{result.dom?.strength > 0.01 ? result.dom.irr : '—'}</div></div>
		<div class="metric-box bg-white"><div class="text-xs text-gray-500 font-semibold uppercase tracking-wide">Dominant Rule</div><div class="text-sm font-bold mt-4 text-gray-800 leading-tight">{result.dom?.strength > 0.01 ? result.dom.then : '—'}</div></div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		<div>
			<h3 class="section-title">Active Rule Firing</h3>
			<div class="space-y-3">
				{#each result.firings.filter((f) => f.strength > 0.01) as f}
					<div class="border rounded-lg p-3 shadow-sm" style="background-color:{condBgColor(f.score)}; border-color:{condColor(f.score)}40">
						<div class="flex justify-between items-start mb-1">
							<div class="font-semibold text-gray-900 text-sm">{f.then}</div>
							<div class="text-xs font-bold px-2 py-1 rounded bg-white border" style="color:{condColor(f.score)}">{f.strength.toFixed(2)}</div>
						</div>
						<div class="text-xs text-gray-600 mb-2">{f.action}</div>
						<div class="w-full bg-white rounded-full h-1.5 overflow-hidden"><div class="h-1.5 rounded-full" style="width:{f.strength * 100}%; background-color:{condColor(f.score)}"></div></div>
					</div>
				{/each}
			</div>
		</div>
		<div>
			<h3 class="section-title">Action Plan Recipe</h3>
			<div class="bg-s5 border-l-4 border-s5b rounded-r-xl p-5 mb-8 shadow-sm">
				<div class="text-base font-medium text-gray-900 leading-relaxed">
					{result.dom?.strength > 0.01 ? result.dom.action : 'Conditions are stable based on current metrics.'}
				</div>
			</div>
		</div>
	</div>
{/if}
