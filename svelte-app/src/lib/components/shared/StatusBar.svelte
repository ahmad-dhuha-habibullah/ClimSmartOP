<script>
	import { onMount } from 'svelte';

	let lastRunTime = $state('Fetching...');
	let lastRunStatus = $state('');
	let lastDbTime = $state('Fetching...');

	const REPO_OWNER = 'ahmad-dhuha-habibullah';
	const REPO_NAME = 'ClimSmartOP';
	const DB_PATH = 'assets/south_sumatra_oilpalm_daily_forecast.db';

	let showAdminModal = $state(false);
	let adminKey = $state('');
	let loading = $state(false);

	onMount(fetchCronStatus);

	async function fetchCronStatus() {
		try {
			const runRes = await fetch(
				`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?per_page=1`
			);
			if (runRes.ok) {
				const runData = await runRes.json();
				if (runData.workflow_runs?.length > 0) {
					const lastRun = runData.workflow_runs[0];
					lastRunTime = new Date(lastRun.updated_at).toLocaleString();
					const status = lastRun.status === 'completed' ? lastRun.conclusion : lastRun.status;
					lastRunStatus = status || '';
				}
			}
			const dbRes = await fetch(
				`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/commits?path=${DB_PATH}&per_page=1`
			);
			if (dbRes.ok) {
				const dbData = await dbRes.json();
				if (dbData.length > 0) {
					lastDbTime = new Date(dbData[0].commit.author.date).toLocaleString();
				}
			}
		} catch (e) {
			console.error('Failed to fetch cron status:', e);
		}
	}

	async function triggerWorkflow() {
		const savedKey = localStorage.getItem('climsmart_admin_key');
		if (savedKey) {
			await executeRemoteCron(savedKey);
		} else {
			showAdminModal = true;
		}
	}

	async function submitAdmin() {
		if (!adminKey.trim()) return;
		showAdminModal = false;
		await executeRemoteCron(adminKey.trim());
		adminKey = '';
	}

	async function executeRemoteCron(token) {
		loading = true;
		try {
			const response = await fetch(
				`https://ktuemkqrelpdaxwpmtax.supabase.co/functions/v1/trigger-apsim`,
				{
					method: 'POST',
					headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
				}
			);
			if (response.ok) {
				localStorage.setItem('climsmart_admin_key', token);
				lastRunTime = 'Triggered!';
				lastRunStatus = 'in_progress';
			} else {
				localStorage.removeItem('climsmart_admin_key');
			}
		} catch (e) {
			console.error(e);
		} finally {
			loading = false;
			setTimeout(fetchCronStatus, 3000);
		}
	}

	function closeModal() {
		showAdminModal = false;
		adminKey = '';
	}
</script>

<div
	class="flex flex-col sm:flex-row justify-between items-center bg-gray-50 border border-gray-200 p-3 rounded-xl shadow-sm mb-6 gap-4"
>
	<div class="flex flex-col sm:flex-row gap-4 sm:gap-8 text-xs sm:text-sm pl-2">
		<div>
			<i class="ti ti-activity text-blue-500 mr-1"></i>
			<span class="text-gray-500 font-semibold uppercase tracking-wider text-[10px]">Action Status:</span>
			<span class="font-bold text-gray-800 ml-1">{lastRunTime}</span>
			<span class="ml-1 text-gray-400">{lastRunStatus}</span>
		</div>
		<div>
			<i class="ti ti-database text-green-500 mr-1"></i>
			<span class="text-gray-500 font-semibold uppercase tracking-wider text-[10px]">DB Sync:</span>
			<span class="font-bold text-gray-800 ml-1">{lastDbTime}</span>
		</div>
	</div>
	<button
		onclick={triggerWorkflow}
		disabled={loading}
		class="w-full sm:w-auto bg-white border border-gray-300 text-gray-700 hover:text-palm-700 hover:border-palm-500 px-4 py-2 rounded-lg text-sm font-bold shadow-sm transition-colors flex items-center justify-center gap-2"
	>
		{#if loading}
			<i class="ti ti-loader animate-spin text-palm-600"></i> Triggering...
		{:else}
			<i class="ti ti-player-play-filled text-palm-600"></i> Manual Override ApsimX Run
		{/if}
	</button>
</div>

{#if showAdminModal}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		role="dialog"
		aria-modal="true"
		class="fixed inset-0 z-[150] flex items-center justify-center bg-black/50"
		onclick={(e) => { if (e.target === e.currentTarget) closeModal(); }}
		onkeydown={(e) => { if (e.key === 'Escape') closeModal(); }}
	>
		<div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
			<div class="flex items-center gap-3 mb-4">
				<div class="w-10 h-10 rounded-full bg-palm-100 flex items-center justify-center text-palm-700">
					<i class="ti ti-lock text-xl"></i>
				</div>
				<h3 class="text-lg font-bold text-gray-900">Admin Authorization</h3>
			</div>
			<p class="text-sm text-gray-500 mb-4">Please enter the administrative key to securely trigger manual ApsimX runs.</p>
			<input
				type="password"
				bind:value={adminKey}
				onkeydown={(e) => e.key === 'Enter' && submitAdmin()}
				class="w-full border border-gray-300 rounded-lg px-4 py-2 mb-6 focus:ring-2 focus:ring-palm-500 outline-none text-sm"
				placeholder="Enter Admin Key"
			/>
			<div class="flex justify-end gap-3">
				<button onclick={closeModal} class="px-4 py-2 text-sm font-semibold text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">Cancel</button>
				<button onclick={submitAdmin} class="px-4 py-2 bg-palm-700 hover:bg-palm-800 text-white text-sm font-bold rounded-lg shadow-sm transition-colors">Authorize & Run</button>
			</div>
		</div>
	</div>
{/if}
