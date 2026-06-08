<script>
	import './layout.css';
	import { onMount } from 'svelte';
	import { initSql, sqlReady } from '$lib/stores/sql.js';
	import Header from '$lib/components/shared/Header.svelte';
	import StatusBar from '$lib/components/shared/StatusBar.svelte';
	import Toast from '$lib/components/shared/Toast.svelte';
	import AiChatWidget from '$lib/components/chat/AiChatWidget.svelte';

	let { children } = $props();

	onMount(() => {
		initSql().catch((e) => console.error('SQL.js init failed:', e));
	});
</script>

<svelte:head>
	<link rel="icon" href="/clim-smart-op-icon.png" type="image/png" />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
	<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css" />
	<title>ClimSmart-OP Platform</title>
</svelte:head>

<Toast />
<div class="w-full flex-grow mx-auto p-4 sm:p-6 lg:p-8">
	<Header sqlReady={$sqlReady} />
	<StatusBar />
	{@render children()}
</div>
<AiChatWidget />
