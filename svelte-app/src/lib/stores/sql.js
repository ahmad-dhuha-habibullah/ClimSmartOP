import { writable } from 'svelte/store';

export const sqlReady = writable(false);
export let SQL_ENGINE = null;

export async function initSql() {
	const initSqlJs = (await import('sql.js')).default;
	SQL_ENGINE = await initSqlJs({
		locateFile: (file) => `/${file}`
	});
	sqlReady.set(true);
}
