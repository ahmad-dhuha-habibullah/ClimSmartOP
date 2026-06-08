<script>
	import Nav from '$lib/components/shared/Nav.svelte';
</script>

<svelte:head>
	<title>ClimSmart-OP Platform Overview</title>
</svelte:head>

<Nav activeTab="overview" />

<div class="mb-6 flex justify-between items-end">
	<div>
		<h2 class="text-lg font-bold text-gray-800 mb-1">Architecture & Implementation Status</h2>
		<p class="text-sm text-gray-500"
			>End-to-End Operational Pipeline showing live integrations and future roadmap modules.</p
		>
	</div>
	<div class="hidden sm:flex gap-3 text-xs font-bold">
		<span class="flex items-center gap-1.5 text-gray-700"
			><span class="w-2.5 h-2.5 rounded-full bg-green-500"></span> Live</span
		>
		<span class="flex items-center gap-1.5 text-gray-400"
			><span class="w-2.5 h-2.5 rounded-full bg-gray-300"></span> Pending</span
		>
	</div>
</div>

<div class="grid grid-cols-1 md:grid-cols-5 gap-4 lg:gap-6 min-h-[450px]">
	<!-- Stage 1 -->
	<div class="pipe-card bg-s1/20 border-s1b/30">
		<div class="pipe-head text-s1b"><i class="ti ti-database text-lg"></i> 1. Data Ingestion</div>
		<div class="pipe-item border-green-200 shadow-sm border-l-4 border-l-green-500"
			><i class="ti ti-world text-s1b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">ECMWF Forecasts</strong><br /><span class="text-gray-500">Historical & Future API</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-cloud text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>BMKG API</strong><br /><span class="text-gray-400">Local 3-day resolution</span></div>
			<span class="badge-pending">PENDING</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-wifi text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>IoT Sensors</strong><br /><span class="text-gray-400">Micro-weather telemetry</span></div>
			<span class="badge-pending">PENDING</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-satellite text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>Sentinel-2</strong><br /><span class="text-gray-400">NDVI / Crop Mapping</span></div>
			<span class="badge-pending">PENDING</span></div
		>
	</div>

	<!-- Stage 2 -->
	<div class="pipe-card bg-s2/20 border-s2b/30">
		<div class="pipe-head text-s2b"><i class="ti ti-temperature text-lg"></i> 2. Climate Prep</div>
		<div class="pipe-item border-blue-200 shadow-sm border-l-4 border-l-blue-500"
			><i class="ti ti-calendar-stats text-s2b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Short/Medium Model</strong><br /><span class="text-gray-500">16-day dynamic horizon</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="pipe-item border-blue-200 shadow-sm border-l-4 border-l-blue-500"
			><i class="ti ti-globe text-s2b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Seasonal Forecast</strong><br /><span class="text-gray-500">6-Month .MET generation</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-chart-line text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>Sub-seasonal</strong><br /><span class="text-gray-400">Ensemble predictions</span></div>
			<span class="badge-pending">PENDING</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-adjustments-alt text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>CMIP Projections</strong><br /><span class="text-gray-400">Long-Term Decadal Models</span></div>
			<span class="badge-pending">PENDING</span></div
		>
	</div>

	<!-- Stage 3 -->
	<div class="pipe-card bg-s3/20 border-s3b/30">
		<div class="pipe-head text-s3b"><i class="ti ti-leaf text-lg"></i> 3. Crop Modeling</div>
		<div class="pipe-item border-purple-200 shadow-sm border-l-4 border-l-purple-500"
			><i class="ti ti-settings text-s3b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">ApsimX Config</strong><br /><span class="text-gray-500">Soil & Crop Params</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div
			class="my-3 text-center py-2.5 bg-white rounded-lg border border-s3b/40 shadow-md relative overflow-hidden flex flex-col items-center justify-center min-h-[60px]"
		>
			<div class="absolute inset-0 bg-gradient-to-r from-s3/20 to-transparent"></div>
			<img
				src="https://raw.githubusercontent.com/APSIMInitiative/ApsimX/9b1e6c5eac8de2326c8d0ff7e79d7e2319e39454/Docs/static/images/ApsimLogo.png"
				alt="ApsimX Logo"
				class="h-6 object-contain relative z-10 mb-1.5"
			/>
			<div class="text-[10px] font-bold text-s3b uppercase relative z-10 leading-none"
				>Oil Palm Simulation</div
			>
		</div>
		<div class="pipe-item border-purple-200 shadow-sm border-l-4 border-l-purple-500"
			><i class="ti ti-server-cog text-s3b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Automated Cron</strong><br /><span class="text-gray-500">Remote Cloud Runs</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="mt-auto pt-3 border-t border-black/10"
			><a
				href="/apsimx"
				class="w-full block text-center text-xs font-bold text-white bg-s3b hover:bg-purple-700 px-3 py-1.5 rounded-md transition-colors shadow-sm"
				>Analyze DB Outputs &rarr;</a
			></div
		>
	</div>

	<!-- Stage 4 -->
	<div class="pipe-card bg-s4/20 border-s4b/30">
		<div class="pipe-head text-s4b"><i class="ti ti-brain text-lg"></i> 4. Decision Support</div>
		<div class="pipe-item border-orange-200 shadow-sm border-l-4 border-l-orange-500"
			><i class="ti ti-database-export text-s4b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Data Extraction</strong><br /><span class="text-gray-500">Parse DB metrics</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="pipe-item border-orange-200 shadow-sm border-l-4 border-l-orange-500"
			><i class="ti ti-chart-area-line text-s4b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Fuzzification</strong><br /><span class="text-gray-500">Map fuzzy variables</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="pipe-item border-orange-200 shadow-sm border-l-4 border-l-orange-500"
			><i class="ti ti-vector-bezier-2 text-s4b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Inference Engine</strong><br /><span class="text-gray-500">Evaluate fuzzy rules</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="mt-auto pt-3 border-t border-black/10"
			><a
				href="/dss"
				class="w-full block text-center text-xs font-bold text-white bg-s4b hover:bg-orange-600 px-3 py-1.5 rounded-md transition-colors shadow-sm"
				>Open DSS Engine &rarr;</a
			></div
		>
	</div>

	<!-- Stage 5 -->
	<div class="pipe-card bg-s5/20 border-s5b/30">
		<div class="pipe-head text-s5b"><i class="ti ti-rocket text-lg"></i> 5. Actions (beta)</div>
		<div class="pipe-item border-teal-200 shadow-sm border-l-4 border-l-teal-500"
			><i class="ti ti-layout-dashboard text-s5b mt-0.5 text-lg"></i>
			<div><strong class="text-gray-900">Web Dashboard</strong><br /><span class="text-gray-500">Maps & Insights</span></div>
			<span class="badge-live">LIVE</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-device-gamepad text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>Edge Devices</strong><br /><span class="text-gray-400">Trigger irrigation hardware</span></div>
			<span class="badge-pending">PENDING</span></div
		>
		<div class="pipe-item pipe-item-pending"
			><i class="ti ti-api text-gray-400 mt-0.5 text-lg"></i>
			<div><strong>API Backend</strong><br /><span class="text-gray-400">RESTful action endpoints</span></div>
			<span class="badge-pending">PENDING</span></div
		>
		<div class="mt-auto pt-3 border-t border-black/10"
			><a
				href="/spatial"
				class="w-full block text-center text-xs font-bold text-white bg-s5b hover:bg-teal-700 px-3 py-1.5 rounded-md transition-colors shadow-sm"
				>View Spatial Map &rarr;</a
			></div
		>
	</div>
</div>
