<script>
	let { activeTab = 'overview' } = $props();

	const tabs = [
		{ id: 'overview', label: 'Platform Overview', icon: 'ti-layout-dashboard', href: '/' },
		{ id: 'apsimx', label: 'ApsimX Analytics', icon: 'ti-database-import', href: '/apsimx' },
		{ id: 'dss', label: 'DSS Engine', icon: 'ti-brain', href: '/dss' },
		{ id: 'spatial', label: 'Spatial & Actions (beta)', icon: 'ti-map-2', href: '/spatial' }
	];
</script>

<div class="flex overflow-x-auto border-b border-gray-200 mb-6 gap-2 px-2">
	{#each tabs as tab}
		<a
			href={tab.href}
			class="main-tab {activeTab === tab.id ? 'active' : ''}"
		>
			<i class="ti {tab.icon} mr-1.5 text-lg align-text-bottom"></i> {tab.label}
		</a>
	{/each}
</div>
