import { writable } from 'svelte/store';

export const apsimContext = writable(null);
export const apsimDisplay = writable('');
export const dbMinDate = writable(null);
export const dbMaxDate = writable(null);
export const todayDate = writable(null);

export const yieldChartInstance = writable(null);
export const laiChartInstance = writable(null);
export const dailyChartInstance = writable(null);
export const dailyGridCharts = writable({});
