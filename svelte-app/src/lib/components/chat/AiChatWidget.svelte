<script>
	import { onMount } from 'svelte';
	import { chatHistory, chatOpen } from '$lib/stores/chat.js';
	import { apsimContext } from '$lib/stores/apsim.js';
	import { activeBlock } from '$lib/stores/estate.js';

	const publishableKey = 'sb_publishable_O8kV6rZ_Cx6v7VeDfmj1sA_oSBkJ68s';
	let inputText = $state('');
	let isLoading = $state(false);
	let messages = $state([
		{ role: 'model', text: 'Hello! I monitor the entire ClimSmart-OP platform. I can see your uploaded databases, your active DSS simulator settings, and which spatial blocks you click on. How can I help?' }
	]);

	function toggle() {
		$chatOpen = !$chatOpen;
	}

	function getSystemPrompt() {
		let ctx = 'Context: You are ClimSmart AI, an Agronomy and Modeling expert. Answer concisely in HTML format (<p>, <strong>, <ul><li>). DO NOT use markdown headers.';
		const ac = $apsimContext;
		if (ac) {
			ctx += `\n\n[ApsimX DATABASE LOADED]\nSimulation Range: ${ac.years}, Avg Yield: ${ac.avgYield} t/ha, Avg LAI: ${ac.avgLAI}, Avg Rain: ${ac.avgRain} mm. Mode: ${ac.isMonthly ? 'Monthly Seasonal' : 'Daily Short-Term'} Resolution.`;
		}
		return ctx;
	}

	function formatMd(text) {
		let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>');
		return html
			.split('\n')
			.map((p) => (p.trim() ? `<p>${p}</p>` : ''))
			.join('');
	}

	async function submitChat() {
		const text = inputText.trim();
		if (!text || isLoading) return;
		messages.push({ role: 'user', text });
		inputText = '';
		isLoading = true;

		const history = $chatHistory.map((m) => ({ role: m.role, parts: [{ text: m.text }] }));
		const payload = {
			systemInstruction: { parts: [{ text: getSystemPrompt() }] },
			contents: [...history, { role: 'user', parts: [{ text }] }]
		};

		try {
			const url = 'https://ktuemkqrelpdaxwpmtax.supabase.co/functions/v1/gemini-proxy';
			const delays = [1000, 2000, 4000, 8000, 16000];
			let reply;
			let lastError;
			for (let i = 0; i <= delays.length; i++) {
				try {
					const response = await fetch(url, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${publishableKey}`, apikey: publishableKey },
						body: JSON.stringify(payload)
					});
					if (!response.ok) throw new Error(`HTTP ${response.status}`);
					const data = await response.json();
					reply = data.candidates?.[0]?.content?.parts?.[0]?.text;
					if (!reply) throw new Error('Invalid response');
					break;
				} catch (e) {
					lastError = e;
					if (i < delays.length) await new Promise((r) => setTimeout(r, delays[i]));
				}
			}
			if (!reply) throw lastError;
			messages.push({ role: 'model', text: reply });
			$chatHistory = [...$chatHistory, { role: 'user', text }, { role: 'model', text: reply }];
		} catch (e) {
			messages.push({ role: 'error', text: 'Connection error. Please try again.' });
		} finally {
			isLoading = false;
		}
	}
</script>

<div class="fixed bottom-6 right-6 z-50 flex flex-col items-end">
	{#if $chatOpen}
		<div
			class="w-[360px] sm:w-[400px] h-[500px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden mb-4"
			style="animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards"
		>
			<div class="bg-gradient-to-r from-palm-800 to-palm-600 p-4 flex justify-between items-center text-white">
				<div class="flex items-center gap-3">
					<div class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center"><i class="ti ti-brain"></i></div>
					<div><h3 class="font-bold text-sm leading-tight">ClimSmart AI</h3><p class="text-[10px] text-palm-100">Data & Context-Aware Expert</p></div>
				</div>
				<button onclick={toggle} aria-label="Close chat" class="text-white/80 hover:text-white p-1 rounded-md hover:bg-white/10 transition-colors"><i class="ti ti-x"></i></button>
			</div>
			<div class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50 text-sm">
				{#each messages as msg}
					{#if msg.role === 'user'}
						<div class="flex gap-3 max-w-[90%] ml-auto justify-end">
							<div class="bg-palm-700 text-white px-3.5 py-2.5 rounded-2xl rounded-tl-sm shadow-sm chat-msg">{@html formatMd(msg.text)}</div>
						</div>
					{:else if msg.role === 'model'}
						<div class="flex gap-3 max-w-[90%]">
							<div class="w-7 h-7 rounded-full bg-palm-100 flex items-center justify-center text-palm-700 shrink-0 mt-0.5"><i class="ti ti-robot text-sm"></i></div>
							<div class="bg-white border border-gray-200 text-gray-800 px-3.5 py-2.5 rounded-2xl rounded-tl-sm shadow-sm chat-msg">{@html formatMd(msg.text)}</div>
						</div>
					{:else}
						<div class="text-center text-xs text-red-500 bg-red-50 p-2 rounded-lg mx-4">{msg.text}</div>
					{/if}
				{/each}
				{#if isLoading}
					<div class="flex gap-3 max-w-[90%]">
						<div class="w-7 h-7 rounded-full bg-palm-100 flex items-center justify-center text-palm-700 shrink-0 mt-0.5"><i class="ti ti-robot text-sm"></i></div>
						<div class="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-1.5">
							<div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
							<div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0.2s"></div>
							<div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay:0.4s"></div>
						</div>
					</div>
				{/if}
			</div>
			<div class="p-3 bg-white border-t border-gray-100">
				<form onsubmit={(e) => { e.preventDefault(); submitChat(); }} class="flex gap-2">
					<input
						type="text"
						bind:value={inputText}
						disabled={isLoading}
						class="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:ring-2 focus:ring-palm-500 focus:border-palm-500 outline-none text-sm transition-all"
						placeholder="Ask about the platform data..."
						autocomplete="off"
					/>
					<button type="submit" disabled={isLoading} aria-label="Send message" class="bg-palm-700 text-white w-10 h-10 rounded-full hover:bg-palm-800 transition-colors flex items-center justify-center shrink-0 disabled:opacity-50 shadow-md"><i class="ti ti-send"></i></button>
				</form>
			</div>
		</div>
	{/if}

	<button
		onclick={toggle}
		aria-label="Open AI chat"
		class="bg-palm-700 text-white w-14 h-14 rounded-full shadow-xl hover:bg-palm-800 transition-transform hover:scale-105 flex items-center justify-center relative"
	>
		<i class="ti ti-message-chatbot text-2xl"></i>
	</button>
</div>
