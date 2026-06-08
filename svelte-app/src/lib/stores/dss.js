import { writable } from 'svelte/store';

export const dssInputs = writable({ swd: 55, trep: 60, lai: 38, ndvi: 60 });
export const dssResult = writable(null);
