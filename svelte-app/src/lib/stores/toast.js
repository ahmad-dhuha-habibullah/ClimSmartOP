import { writable } from 'svelte/store';

export const toasts = writable([]);

let idCounter = 0;

export function showToast(message, type = 'info') {
	const id = ++idCounter;
	toasts.update((t) => [...t, { id, message, type }]);
	setTimeout(() => {
		toasts.update((t) => t.filter((x) => x.id !== id));
	}, 4500);
}
