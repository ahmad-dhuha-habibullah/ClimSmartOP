<script>
	import { onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import Nav from '$lib/components/shared/Nav.svelte';
	import { SQL_ENGINE, sqlReady } from '$lib/stores/sql.js';
	import { apsimContext } from '$lib/stores/apsim.js';
	import { showToast } from '$lib/stores/toast.js';

	let Chart;
	let loaded = $state(false);
	let loading = $state(false);
	let displayName = $state('');
	let activeSubTab = $state('annual');

	let statYears = $state('-');
	let statYield = $state('-');
	let statLai = $state('-');
	let statRain = $state('-');

	let tableData = $state([]);
	let annualChartData = $state(null);
	let dailyChartData = $state(null);
	let gridChartData = $state(null);
	let isMonthly = $state(false);

	let dateMin = $state('');
	let dateMax = $state('');
	let dbMin = $state(null);
	let dbMax = $state(null);
	let simToday = $state(null);

	let yieldChart = null;
	let laiChart = null;
	let dailyChart = null;
	let gridCharts = {};

	onMount(async () => {
		const mod = await import('chart.js/auto');
		await import('chartjs-adapter-date-fns');
		await import('chartjs-plugin-annotation');
		Chart = mod.Chart || mod.default;
	});

	async function getTrueToday() {
		const now = new Date();
		return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
	}

	function getAnnotationConfig() {
		if (!simToday) return {};
		return {
			annotations: {
				todayLine: {
					type: 'line',
					scaleID: 'x',
					value: simToday,
					borderColor: 'rgb(239, 68, 68)',
					borderWidth: 2,
					borderDash: [5, 5],
					label: {
						content: 'TODAY',
						display: true,
						position: 'start',
						backgroundColor: 'rgba(239, 68, 68, 0.9)',
						color: 'white',
						font: { size: 9, weight: 'bold' }
					}
				}
			}
		};
	}

	function destroyCharts() {
		if (yieldChart) { yieldChart.destroy(); yieldChart = null; }
		if (laiChart) { laiChart.destroy(); laiChart = null; }
		if (dailyChart) { dailyChart.destroy(); dailyChart = null; }
		Object.values(gridCharts).forEach((c) => c?.destroy());
		gridCharts = {};
	}

	async function renderAnnualCharts(data) {
		await tick();
		if (!Chart) return;

		const labels = data.map((d) => d.Year);
		const yields = data.map((d) => d.Yield);
		const rain = data.map((d) => d.Rain);
		const lais = data.map((d) => d.LAI);

		const ctxY = document.getElementById('yieldChart');
		if (ctxY) {
			yieldChart = new Chart(ctxY.getContext('2d'), {
				type: 'bar',
				data: {
					labels,
					datasets: [
						{ label: 'FFB Yield (t/ha)', data: yields, backgroundColor: '#3B6D11', yAxisID: 'y', borderRadius: 4 },
						{ label: 'Annual Rain (mm)', data: rain, type: 'line', borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', borderWidth: 2, yAxisID: 'y1', fill: true, tension: 0.3 }
					]
				},
				options: {
					responsive: true, maintainAspectRatio: false,
					scales: {
						y: { type: 'linear', position: 'left', title: { display: true, text: 'Yield (t/ha)' } },
						y1: { type: 'linear', position: 'right', title: { display: true, text: 'Rain (mm)' }, grid: { drawOnChartArea: false } },
						x: { grid: { display: false } }
					},
					plugins: { legend: { position: 'top', labels: { boxWidth: 12 } } }
				}
			});
		}

		const ctxL = document.getElementById('laiChart');
		if (ctxL) {
			laiChart = new Chart(ctxL.getContext('2d'), {
				type: 'line',
				data: {
					labels,
					datasets: [
						{ label: 'Peak LAI', data: lais, borderColor: '#059669', backgroundColor: 'rgba(5, 150, 105, 0.2)', borderWidth: 2, fill: true, tension: 0.4 }
					]
				},
				options: {
					responsive: true, maintainAspectRatio: false,
					scales: {
						y: { min: 0, title: { display: true, text: 'LAI (m²/m²)' } },
						x: { grid: { display: false } }
					},
					plugins: { legend: { display: false } }
				}
			});
		}
	}

	async function renderDailyChart(data) {
		await tick();
		if (!Chart) return;

		const labels = data.map((d) => (typeof d.Date === 'string' ? d.Date.split(' ')[0] : d.Date));
		const lais = data.map((d) => d.LAI || 0);
		const rain = data.map((d) => d.Rain || 0);

		const ctx = document.getElementById('dailyChart');
		if (!ctx) return;

		dailyChart = new Chart(ctx.getContext('2d'), {
			type: 'line',
			data: {
				labels,
				datasets: [
					{ label: isMonthly ? 'Monthly Rain (mm)' : 'Daily Rain (mm)', data: rain, type: 'bar', backgroundColor: 'rgba(59, 130, 246, 0.4)', yAxisID: 'y1', barPercentage: 1.0, categoryPercentage: 1.0 },
					{ label: isMonthly ? 'Monthly LAI' : 'Daily LAI', data: lais, type: 'line', borderColor: '#059669', borderWidth: 1.5, yAxisID: 'y', pointRadius: 0, tension: 0.2 }
				]
			},
			options: {
				responsive: true, maintainAspectRatio: false,
				scales: {
					y: { type: 'linear', position: 'left', title: { display: true, text: 'LAI' }, min: 0 },
					y1: { type: 'linear', position: 'right', title: { display: true, text: 'Rain (mm)' }, grid: { drawOnChartArea: false }, min: 0, suggestedMax: 100 },
					x: { type: 'time', time: { unit: isMonthly ? 'month' : 'day' }, grid: { display: false }, ticks: { maxTicksLimit: 12 } }
				},
				plugins: { legend: { position: 'top', labels: { boxWidth: 12 } }, annotation: getAnnotationConfig() },
				interaction: { mode: 'index', intersect: false }
			}
		});
	}

	async function renderGridCharts(data) {
		await tick();
		if (!Chart) return;

		const dates = data.map((d) => (typeof d.Date === 'string' ? d.Date.split(' ')[0] : d.Date));

		const subplots = [
			{ key: 'age', dataKey: 'Age', color: '#639922' },
			{ key: 'lai', dataKey: 'LAI', color: '#16a34a' },
			{ key: 'fronds', dataKey: 'Fronds', color: '#2563eb' },
			{ key: 'bunches', dataKey: 'Bunches', color: '#d97706' },
			{ key: 'yield', dataKey: 'AnnualYield', color: '#dc2626' },
			{ key: 'bunchsize', dataKey: 'BunchSize', color: '#9333ea' },
			{ key: 'harvestffb', dataKey: 'HarvestFFB', color: '#059669' },
			{ key: 'rain', dataKey: 'Rain', color: '#2563eb', isBar: true },
			{ key: 'es', dataKey: 'Es', color: '#0d9488' },
			{ key: 'ep', dataKey: 'EP', color: '#10b981' },
			{ key: 'understoryep', dataKey: 'UnderstoryEP', color: '#84cc16' },
			{ key: 'no3_1', dataKey: 'NO3_1', color: '#ea580c' },
			{ key: 'no3_2', dataKey: 'NO3_2', color: '#f97316' },
			{ key: 'no3_3', dataKey: 'NO3_3', color: '#fb923c' },
			{ key: 'om_wt', dataKey: 'OM_Wt', color: '#4f46e5' },
			{ key: 'om_n', dataKey: 'OM_N', color: '#6366f1' },
			{ key: 'rootgrowth', dataKey: 'RootGrowth', color: '#06b6d4' },
			{ key: 'stemgrowth', dataKey: 'StemGrowth', color: '#0891b2' },
			{ key: 'frondgrowth', dataKey: 'FrondGrowth', color: '#0284c7' },
			{ key: 'bunchgrowth', dataKey: 'BunchGrowth', color: '#4338ca' }
		];

		subplots.forEach((plot) => {
			const canvas = document.getElementById(`gridChart-${plot.key}`);
			if (!canvas) return;
			if (gridCharts[plot.key]) gridCharts[plot.key].destroy();

			const series = data.map((d) => d[plot.dataKey] ?? 0);
			gridCharts[plot.key] = new Chart(canvas.getContext('2d'), {
				type: plot.isBar ? 'bar' : 'line',
				data: {
					labels: dates,
					datasets: [{
						label: plot.key,
						data: series,
						borderColor: plot.color,
						backgroundColor: plot.isBar ? plot.color : `${plot.color}15`,
						borderWidth: 1.2,
						pointRadius: 0,
						fill: !plot.isBar,
						tension: 0.1
					}]
				},
				options: {
					responsive: true, maintainAspectRatio: false,
					scales: {
						x: { type: 'time', time: { unit: isMonthly ? 'month' : 'day' }, display: true, grid: { display: false }, ticks: { maxTicksLimit: 4, font: { size: 9 } } },
						y: { display: true, grid: { color: '#f3f4f6' }, ticks: { font: { size: 9 } } }
					},
					plugins: { legend: { display: false }, annotation: getAnnotationConfig() }
				}
			});
		});
	}

	async function loadDbFromUrl(url, name) {
		if (!$sqlReady || !Chart) {
			showToast('Please wait for the database engine to initialize.', 'error');
			return;
		}
		loading = true;
		try {
			let response = await fetch(url);
			if (response.status === 404 && url.includes('/main/')) {
				response = await fetch(url.replace('/main/', '/master/'));
			}
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			const buf = await response.arrayBuffer();
			const db = new SQL_ENGINE.Database(new Uint8Array(buf));
			await analyzeDB(db, name);
		} catch (e) {
			console.error(e);
			showToast('Database not found. Verify that the Automated Cron has completed.', 'error');
		} finally {
			loading = false;
		}
	}

	function handleFileUpload(event) {
		const file = event.target.files?.[0];
		if (!file || !$sqlReady || !Chart) {
			showToast('Please wait for the database engine to initialize.', 'error');
			return;
		}
		const reader = new FileReader();
		reader.onload = async () => {
			try {
				const db = new SQL_ENGINE.Database(new Uint8Array(reader.result));
				await analyzeDB(db, file.name.replace(/\.[^/.]+$/, ''));
			} catch (e) {
				showToast('Error parsing database. Ensure valid ApsimX SQLite.', 'error');
			}
		};
		reader.readAsArrayBuffer(file);
	}

	async function analyzeDB(db, name) {
		try {
			const query = `SELECT "Clock.Today.Year" as Year, "OilPalm.Age" as Age, "OilPalm.LAI" as LAI, "AnnualRain" as Rain, "Calculations.Script.AnnualYield" as Yield, "AnnualET" as ET FROM AnnualOutput ORDER BY "Clock.Today.Year" ASC`;
			const res = db.exec(query);
			if (res.length === 0) throw new Error('AnnualOutput table is empty.');
			const columns = res[0].columns;
			const data = res[0].values.map((row) => {
				let obj = {};
				columns.forEach((col, idx) => (obj[col] = row[idx]));
				return obj;
			});

			const years = data.map((d) => d.Year);
			const validYields = data.map((d) => d.Yield).filter((y) => y !== null && y > 0);
			const avgYield = validYields.length > 0 ? (validYields.reduce((a, b) => a + b, 0) / validYields.length).toFixed(1) : 0;
			const validLAI = data.map((d) => d.LAI).filter((l) => l !== null);
			const avgLAI = validLAI.length > 0 ? (validLAI.reduce((a, b) => a + b, 0) / validLAI.length).toFixed(2) : 0;
			const validRain = data.map((d) => d.Rain).filter((r) => r !== null);
			const avgRain = validRain.length > 0 ? Math.round(validRain.reduce((a, b) => a + b, 0) / validRain.length) : 0;

			statYears = `${years[0]} - ${years[years.length - 1]}`;
			statYield = avgYield;
			statLai = avgLAI;
			statRain = avgRain;
			tableData = [...data].reverse();
			annualChartData = data;
			displayName = name;

			simToday = await getTrueToday();
			const monthly = await analyzeDailyMonthly(db, name);
			isMonthly = monthly;

			apsimContext.set({
				years: `${years[0]}-${years[years.length - 1]}`,
				avgYield,
				avgLAI,
				avgRain,
				isMonthly: monthly
			});

			loaded = true;
			await tick();
			await renderAnnualCharts(data);
			if (dailyChartData) await renderDailyChart(dailyChartData);

			showToast(`Successfully loaded ${name}! (${monthly ? 'Monthly' : 'Daily'} mode)`, 'success');
		} catch (err) {
			console.error(err);
			showToast('Could not process file: ' + err.message, 'error');
		}
	}

	async function analyzeDailyMonthly(db, name) {
		try {
			const tablesRes = db.exec(`SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('_Units','_Checkpoints','_Simulations','_Messages','_InitialConditions','AnnualOutput') AND name NOT LIKE 'sqlite_%'`);
			if (tablesRes.length === 0) return false;
			const targetTable = tablesRes[0].values[0][0];
			const colsRes = db.exec(`PRAGMA table_info("${targetTable}")`);
			if (colsRes.length === 0) return false;
			const columns = colsRes[0].values.map((v) => v[1]);

			const colMap = {
				Date: ['Clock.Today', 'Today', 'Date'],
				Age: ['OilPalm.Age', 'Age'],
				LAI: ['OilPalm.LAI', 'LAI'],
				Fronds: ['Calculations.Script.AnnualFronds', 'AnnualFronds'],
				Bunches: ['Calculations.Script.AnnualBunches', 'AnnualBunches'],
				AnnualYield: ['Calculations.Script.AnnualYield', 'AnnualYield'],
				BunchSize: ['Calculations.Script.AnnualBunchSize', 'AnnualBunchSize'],
				HarvestFFB: ['OilPalm.HarvestFFB', 'HarvestFFB'],
				Rain: ['Weather.Rain', 'Rain'],
				Es: ['Soil.SoilWater.Es', 'Es'],
				EP: ['OilPalm.EP', 'EP'],
				UnderstoryEP: ['OilPalm.UnderstoryEP', 'UnderstoryEP'],
				NO3_1: ['Soil.NO3.kgha(1)'],
				NO3_2: ['Soil.NO3.kgha(2)'],
				NO3_3: ['Soil.NO3.kgha(3)'],
				OM_Wt: ['SurfaceOM.Wt'],
				OM_N: ['SurfaceOM.N'],
				RootGrowth: ['OilPalm.RootGrowth'],
				StemGrowth: ['OilPalm.StemGrowth'],
				FrondGrowth: ['OilPalm.FrondGrowth'],
				BunchGrowth: ['OilPalm.BunchGrowth']
			};

			let selectFields = [];
			for (const [key, aliases] of Object.entries(colMap)) {
				const matched = aliases.find((a) => columns.includes(a));
				selectFields.push(matched ? `"${matched}" as ${key}` : `NULL as ${key}`);
			}

			const query = `SELECT ${selectFields.join(', ')} FROM "${targetTable}" ORDER BY 1 ASC`;
			const res = db.exec(query);
			if (res.length === 0) return false;
			const outCols = res[0].columns;
			const data = res[0].values.map((row) => {
				let obj = {};
				outCols.forEach((c, i) => (obj[c] = row[i]));
				return obj;
			});

			let monthly = false;
			if (data.length > 1) {
				const d1 = new Date(data[0].Date);
				const d2 = new Date(data[1].Date);
				if (Math.abs(d2 - d1) / 86400000 > 15 || targetTable.toLowerCase().includes('monthly')) {
					monthly = true;
				}
			}

			const dates = data.map((d) => (typeof d.Date === 'string' ? d.Date.split(' ')[0] : d.Date));
			if (dates.length > 0) {
				dbMin = dates[0];
				dbMax = dates[dates.length - 1];
				dateMin = dbMin;
				dateMax = dbMax;
			}

			const forecastData = data.filter((d) => {
				const ds = typeof d.Date === 'string' ? d.Date.split(' ')[0] : d.Date;
				return ds >= simToday;
			});
			let metricData = forecastData;
			if (metricData.length === 0 && data.length > 0) {
				metricData = data.slice(-(monthly ? 1 : 15));
			}

			if (metricData.length > 0) {
				const avgR = metricData.reduce((s, d) => s + (d.Rain || 0), 0) / metricData.length;
				const avgEP = metricData.reduce((s, d) => s + (d.EP || 0), 0) / metricData.length;
				const avgEs = metricData.reduce((s, d) => s + (d.Es || 0), 0) / metricData.length;
				const avgL = metricData.reduce((s, d) => s + (d.LAI || 0), 0) / metricData.length;
				let swdProxy = Math.max(0, (avgEP + avgEs - avgR) * (monthly ? 30 : 1));
				swdProxy = Math.min(150, swdProxy * (monthly ? 1 : 15));
				let trepProxy = Math.min(1.0, avgEP / (avgEP + avgEs + 0.001)) * 100;
				let ndviProxy = (0.3 + 0.5 * (1 - Math.exp(-0.5 * avgL))) * 100;

				apsimContext.update((ctx) => ({
					...ctx,
					forecastMetrics: { swd: swdProxy, trep: trepProxy, lai: avgL * 10, ndvi: ndviProxy }
				}));
			}

			const skipFactor = monthly ? 1 : 5;
			const processed = [];
			for (let i = 0; i < data.length; i += skipFactor) processed.push(data[i]);

			dailyChartData = processed;
			gridChartData = processed;
			return monthly;
		} catch (e) {
			console.warn('Could not extract diagnostics:', e);
			return false;
		}
	}

	$effect(() => {
		if (activeSubTab === 'daily-grid' && gridChartData && Chart) {
			renderGridCharts(gridChartData);
		}
	});

	function pushToDSS() {
		const ctx = $apsimContext;
		if (!ctx?.forecastMetrics) return;
		const m = ctx.forecastMetrics;
		const inputs = { swd: Math.round(m.swd), trep: Math.round(m.trep), lai: Math.round(m.lai), ndvi: Math.round(m.ndvi) };
		sessionStorage.setItem('dss_inputs', JSON.stringify(inputs));
		sessionStorage.setItem('dss_is_monthly', String(ctx.isMonthly));
		goto('/dss');
	}
</script>

<svelte:head>
	<title>ApsimX Analytics - ClimSmart-OP</title>
</svelte:head>

<Nav activeTab="apsimx" />

{#if !loaded}
	<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
		<div class="card flex flex-col h-full">
			<div class="flex items-center gap-3 mb-2">
				<img
					src="https://raw.githubusercontent.com/APSIMInitiative/ApsimX/9b1e6c5eac8de2326c8d0ff7e79d7e2319e39454/Docs/static/images/ApsimLogo.png"
					alt="ApsimX Logo"
					class="h-6 object-contain"
				/>
				<h3 class="text-lg font-bold text-gray-800">Cloud Databases</h3>
			</div>
			<p class="text-sm text-gray-500 mb-4">Select an available simulation database dynamically updated by Automated Cron.</p>
			<div class="flex flex-col gap-3 flex-grow">
				<button
					onclick={() => loadDbFromUrl('https://raw.githubusercontent.com/ahmad-dhuha-habibullah/ClimSmartOP/main/assets/south_sumatra_oilpalm_daily_forecast.db', 'south_sumatra_oilpalm_daily_forecast')}
					disabled={loading}
					class="text-left px-4 py-3 bg-gray-50 hover:bg-palm-50 border border-gray-200 hover:border-palm-400 rounded-xl transition-all group flex items-center justify-between"
				>
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-lg bg-white text-palm-600 shadow flex items-center justify-center group-hover:bg-palm-600 group-hover:text-white transition-colors"><i class="ti ti-database text-lg"></i></div>
						<div>
							<div class="text-sm font-bold text-gray-800 group-hover:text-palm-800 truncate">south_sumatra_oilpalm_daily_forecast</div>
							<div class="text-[10px] text-gray-500">Standard 16-Day Simulation</div>
						</div>
					</div>
					<i class="ti ti-arrow-right text-gray-400 group-hover:text-palm-600"></i>
				</button>
				<button
					onclick={() => loadDbFromUrl('https://raw.githubusercontent.com/ahmad-dhuha-habibullah/ClimSmartOP/main/assets/south_sumatra_oilpalm_seasonal_forecast.db', 'south_sumatra_oilpalm_seasonal_forecast')}
					disabled={loading}
					class="text-left px-4 py-3 bg-gray-50 hover:bg-palm-50 border border-gray-200 hover:border-palm-400 rounded-xl transition-all group flex items-center justify-between"
				>
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-lg bg-white text-palm-600 shadow flex items-center justify-center group-hover:bg-palm-600 group-hover:text-white transition-colors"><i class="ti ti-database text-lg"></i></div>
						<div>
							<div class="text-sm font-bold text-gray-800 group-hover:text-palm-800 truncate">south_sumatra_oilpalm_seasonal_forecast</div>
							<div class="text-[10px] text-gray-500">6-Month Seasonal Forecast Resolution</div>
						</div>
					</div>
					<i class="ti ti-arrow-right text-gray-400 group-hover:text-palm-600"></i>
				</button>
			</div>
		</div>
		<label for="db-upload" class="card upload-zone flex flex-col items-center justify-center py-12 bg-white cursor-pointer relative h-full transition-colors">
			<input id="db-upload" type="file" accept=".db,.sqlite,.sqlite3" class="hidden" onchange={handleFileUpload} />
			<div class="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4"><i class="ti ti-upload text-3xl"></i></div>
			<h3 class="text-lg font-bold text-gray-800 mb-1">Custom Upload</h3>
			<p class="text-sm text-gray-500 mb-4 text-center px-4">Have your own simulation? Drag and drop an ApsimX SQLite file here.</p>
			<div class="text-xs font-semibold bg-gray-100 text-gray-500 px-3 py-1 rounded-full flex items-center gap-2">
				<i class="ti ti-lock"></i> Local DB Engine Processing
			</div>
		</label>
	</div>
{:else}
	<div class="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-4 gap-4">
		<div class="flex items-center gap-4">
			<img
				src="https://raw.githubusercontent.com/APSIMInitiative/ApsimX/9b1e6c5eac8de2326c8d0ff7e79d7e2319e39454/Docs/static/images/ApsimLogo.png"
				alt="ApsimX Logo"
				class="h-10 hidden sm:block object-contain"
			/>
			<div>
				<h2 class="text-xl font-bold text-gray-900">Simulation Results Overview</h2>
				<div class="flex items-center gap-3 mt-1">
					<p class="text-sm text-gray-500">Loaded: <strong>{displayName}</strong></p>
					<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold {isMonthly ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-green-50 text-green-700 border border-green-200'}">
						{isMonthly ? 'Monthly' : 'Daily'} Data Mode
					</span>
					<button onclick={() => { destroyCharts(); loaded = false; }} class="text-[10px] font-bold bg-gray-200 text-gray-600 hover:bg-gray-800 hover:text-white px-2 py-1 rounded transition-colors uppercase tracking-wider">Change Data</button>
				</div>
			</div>
		</div>
		<button
			onclick={pushToDSS}
			class="bg-palm-700 hover:bg-palm-800 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow flex items-center gap-2 transition ml-auto sm:ml-0"
		>
			<i class="ti ti-arrow-right"></i> Send Forecast to DSS
		</button>
	</div>

	<div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
		<div class="metric-box"><div class="absolute top-0 left-0 w-full h-1 bg-blue-500"></div><div class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Sim Years</div><div class="text-2xl font-black text-gray-800">{statYears}</div></div>
		<div class="metric-box"><div class="absolute top-0 left-0 w-full h-1 bg-green-500"></div><div class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Avg FFB Yield</div><div class="text-2xl font-black text-gray-800 font-mono">{statYield} <span class="text-sm text-gray-500 font-sans font-medium">t/ha</span></div></div>
		<div class="metric-box"><div class="absolute top-0 left-0 w-full h-1 bg-palm-500"></div><div class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Avg Peak LAI</div><div class="text-2xl font-black text-gray-800 font-mono">{statLai}</div></div>
		<div class="metric-box"><div class="absolute top-0 left-0 w-full h-1 bg-amber-500"></div><div class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">Avg Annual Rain</div><div class="text-2xl font-black text-gray-800 font-mono">{statRain} <span class="text-sm text-gray-500 font-sans font-medium">mm</span></div></div>
	</div>

	{#if dbMin}
		<div class="flex flex-wrap items-center justify-between gap-4 mb-6 bg-white p-3 rounded-xl border border-gray-200 shadow-sm">
			<div class="text-sm font-bold text-gray-700 flex items-center gap-2"><i class="ti ti-calendar-time text-lg text-palm-600"></i> Global Timeline Zoom:</div>
			<div class="flex flex-wrap items-center gap-2">
				<input type="date" bind:value={dateMin} min={dbMin} max={dbMax} class="text-sm border border-gray-300 rounded-md px-3 py-1.5" />
				<span class="text-gray-400 text-xs font-bold uppercase">to</span>
				<input type="date" bind:value={dateMax} min={dbMin} max={dbMax} class="text-sm border border-gray-300 rounded-md px-3 py-1.5" />
			</div>
		</div>
	{/if}

	<div class="flex border-b border-gray-200 mb-6 gap-2 px-2 bg-white p-2 rounded-xl border shadow-sm">
		<button class="px-4 py-2 text-xs font-semibold rounded-lg transition-all {activeSubTab === 'annual' ? 'text-palm-800 bg-palm-50 shadow-sm border border-palm-100' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'}" onclick={() => (activeSubTab = 'annual')}>
			<i class="ti ti-calendar-event mr-1 text-sm align-text-bottom"></i> Key Annual Trends
		</button>
		<button class="px-4 py-2 text-xs font-semibold rounded-lg transition-all {activeSubTab === 'daily-grid' ? 'text-palm-800 bg-palm-50 shadow-sm border border-palm-100' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'}" onclick={() => (activeSubTab = 'daily-grid')}>
			<i class="ti ti-grid-pattern mr-1 text-sm align-text-bottom"></i> {isMonthly ? 'Monthly' : 'Daily'} Multi-Plot Diagnostic Grid
		</button>
	</div>

	{#if activeSubTab === 'annual' && annualChartData}
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			<div class="card"><h3 class="section-title">Yield vs Rainfall Trend</h3><div class="relative h-[250px] w-full"><canvas id="yieldChart"></canvas></div></div>
			<div class="card"><h3 class="section-title">Canopy LAI Trend</h3><div class="relative h-[250px] w-full"><canvas id="laiChart"></canvas></div></div>
		</div>

		{#if dailyChartData}
			<div class="card mb-8">
				<h3 class="section-title">{isMonthly ? 'Monthly' : 'Daily'} Summary (Rainfall & LAI)</h3>
				<div class="relative h-[250px] w-full"><canvas id="dailyChart"></canvas></div>
			</div>
		{/if}

		<div class="card">
			<h3 class="section-title">Raw Annual Output Table</h3>
			<div class="overflow-x-auto max-h-[300px] border border-gray-100 rounded-lg">
				<table class="data-table whitespace-nowrap">
					<thead class="sticky top-0 bg-gray-50 shadow-sm">
						<tr><th>Year</th><th>Age (yr)</th><th>Rain (mm)</th><th>Max LAI</th><th>Yield (t/ha)</th><th>ET (mm)</th></tr>
					</thead>
					<tbody>
						{#each tableData as d}
							<tr class="hover:bg-gray-50 transition-colors">
								<td class="px-4 py-2 font-medium text-gray-900">{d.Year}</td>
								<td class="px-4 py-2">{(d.Age || 0).toFixed(1)}</td>
								<td class="px-4 py-2">{Math.round(d.Rain || 0)}</td>
								<td class="px-4 py-2 font-mono">{(d.LAI || 0).toFixed(2)}</td>
								<td class="px-4 py-2 font-mono font-semibold text-palm-700">{(d.Yield || 0).toFixed(1)}</td>
								<td class="px-4 py-2">{Math.round(d.ET || 0)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}

	{#if activeSubTab === 'daily-grid' && gridChartData}
		<div class="mb-4 bg-palm-50 border border-palm-100 p-4 rounded-xl text-sm text-palm-800 flex items-center gap-3">
			<i class="ti ti-chart-infographic text-2xl"></i>
			<div><strong>{isMonthly ? 'Monthly' : 'Daily'} Diagnostic View</strong><br />The timeline runs sequentially. Red dashed line indicates the split between historical context and forecast horizon.</div>
		</div>
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
			{#each [
				{ key: 'age', title: 'Oil Palm Age' },
				{ key: 'lai', title: 'Oil Palm LAI' },
				{ key: 'fronds', title: 'Calculations.Script.AnnualFronds' },
				{ key: 'bunches', title: 'Calculations.Script.AnnualBunches' },
				{ key: 'yield', title: 'Calculations.Script.AnnualYield' },
				{ key: 'bunchsize', title: 'Calculations.Script.AnnualBunchSize' },
				{ key: 'harvestffb', title: 'OilPalm.HarvestFFB' },
				{ key: 'rain', title: 'Weather.Rain' },
				{ key: 'es', title: 'Soil.SoilWater.Es' },
				{ key: 'ep', title: 'OilPalm.EP' },
				{ key: 'understoryep', title: 'OilPalm.UnderstoryEP' },
				{ key: 'no3_1', title: 'Soil.NO3.kgha(1)' },
				{ key: 'no3_2', title: 'Soil.NO3.kgha(2)' },
				{ key: 'no3_3', title: 'Soil.NO3.kgha(3)' },
				{ key: 'om_wt', title: 'SurfaceOM.Wt' },
				{ key: 'om_n', title: 'SurfaceOM.N' },
				{ key: 'rootgrowth', title: 'OilPalm.RootGrowth' },
				{ key: 'stemgrowth', title: 'OilPalm.StemGrowth' },
				{ key: 'frondgrowth', title: 'OilPalm.FrondGrowth' },
				{ key: 'bunchgrowth', title: 'OilPalm.BunchGrowth' }
			] as plot}
				<div class="card p-4 flex flex-col min-h-[220px]">
					<span class="text-xs font-bold text-gray-500 uppercase truncate">{plot.title}</span>
					<div class="flex-grow mt-2 relative"><canvas id="gridChart-{plot.key}"></canvas></div>
				</div>
			{/each}
		</div>
	{/if}
{/if}
