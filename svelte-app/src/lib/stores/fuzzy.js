export function trap(x, a, b, c, d) {
	if (x <= a || x >= d) return 0;
	if (x >= b && x <= c) return 1;
	if (x < b) return (x - a) / (b - a);
	return (d - x) / (d - c);
}

export function tri(x, a, b, c) {
	if (x <= a || x >= c) return 0;
	if (x === b) return 1;
	if (x < b) return (x - a) / (b - a);
	return (c - x) / (c - b);
}

export const SWD_MF = [
	{ name: 'Deficit', color: '#E24B4A', fn: (x) => trap(x, 0, 0, 30, 60) },
	{ name: 'Low', color: '#EF9F27', fn: (x) => tri(x, 30, 60, 100) },
	{ name: 'Optimal', color: '#639922', fn: (x) => tri(x, 60, 80, 120) },
	{ name: 'High', color: '#185FA5', fn: (x) => tri(x, 100, 120, 150) },
	{ name: 'Excess', color: '#A32D2D', fn: (x) => trap(x, 130, 145, 150, 150) }
];
export const TREP_MF = [
	{ name: 'Deficit', color: '#E24B4A', fn: (x) => trap(x, 0, 0, 40, 55) },
	{ name: 'Low', color: '#EF9F27', fn: (x) => tri(x, 40, 58, 72) },
	{ name: 'Optimal', color: '#639922', fn: (x) => tri(x, 60, 80, 95) },
	{ name: 'High', color: '#185FA5', fn: (x) => tri(x, 88, 95, 100) },
	{ name: 'Anaerobic', color: '#A32D2D', fn: (x) => trap(x, 98, 100, 100, 100) }
];
export const LAI_MF = [
	{ name: 'Stressed', color: '#E24B4A', fn: (x) => trap(x, 0, 0, 22, 35) },
	{ name: 'Suboptimal', color: '#EF9F27', fn: (x) => tri(x, 22, 33, 48) },
	{ name: 'Optimal', color: '#639922', fn: (x) => tri(x, 38, 52, 68) },
	{ name: 'High', color: '#185FA5', fn: (x) => trap(x, 60, 72, 85, 85) }
];
export const NDVI_MF = [
	{ name: 'Stressed', color: '#E24B4A', fn: (x) => trap(x, 30, 30, 48, 58) },
	{ name: 'Normal', color: '#EF9F27', fn: (x) => tri(x, 50, 62, 75) },
	{ name: 'Good', color: '#639922', fn: (x) => tri(x, 65, 75, 88) },
	{ name: 'Vigorous', color: '#185FA5', fn: (x) => trap(x, 80, 88, 95, 95) }
];

export const RULES_DAILY = [
	{ if: { swd: 'Deficit', trep: 'Deficit', ndvi: 'Stressed' }, then: 'Critical stress', score: 8, irr: 'Emergency', action: 'Irrigate 30mm immediately. Hold all fertiliser.' },
	{ if: { swd: 'Deficit', trep: 'Deficit', ndvi: 'Normal' }, then: 'Severe stress', score: 18, irr: 'Urgent', action: 'Irrigate 25mm within 24h. Monitor bunch development.' },
	{ if: { swd: 'Deficit', trep: 'Low', ndvi: 'Stressed' }, then: 'Moderate stress', score: 28, irr: 'High', action: 'Irrigate 18mm. Inspect for pest/disease pressure.' },
	{ if: { swd: 'Deficit', trep: 'Low', ndvi: 'Normal' }, then: 'Low stress', score: 40, irr: 'Moderate', action: 'Schedule irrigation in 48h. Check foliar N.' },
	{ if: { swd: 'Low', trep: 'Low', ndvi: 'Stressed' }, then: 'Moderate stress', score: 32, irr: 'High', action: 'Irrigate 15mm. Scout for Ganoderma.' },
	{ if: { swd: 'Low', trep: 'Low', ndvi: 'Normal' }, then: 'Suboptimal', score: 48, irr: 'Moderate', action: 'Monitor. Apply K fertiliser if schedule due.' },
	{ if: { swd: 'Optimal', trep: 'Optimal', ndvi: 'Normal' }, then: 'Good', score: 72, irr: 'Low', action: 'Optimal. Proceed with planned schedule.' },
	{ if: { swd: 'Optimal', trep: 'Optimal', ndvi: 'Good' }, then: 'Excellent', score: 85, irr: 'None', action: 'Peak condition. Prepare harvest logistics.' },
	{ if: { swd: 'High', trep: 'High', ndvi: 'Normal' }, then: 'Drainage risk', score: 35, irr: 'Drain', action: 'Open drainage channels. Delay N application.' },
	{ if: { swd: 'Excess', trep: 'Optimal', ndvi: 'Stressed' }, then: 'Anaerobic risk', score: 22, irr: 'Drain', action: 'Emergency drainage. Inspect frond bases.' }
];

export const SEASONAL_RULES = [
	{ if: { swd: 'Deficit', trep: 'Deficit', ndvi: 'Stressed' }, then: 'Severe Drought Season Expected', score: 15, irr: 'Max Prep', action: 'Secure long-term water rights. Delay major fertilizer procurement to avoid loss. Plan for lower harvest labor.' },
	{ if: { swd: 'Deficit', trep: 'Low', ndvi: 'Normal' }, then: 'Dry Season Anticipated', score: 35, irr: 'High Prep', action: 'Procure organic mulch/empty fruit bunches (EFB) to retain soil moisture. Shift N-P-K applications.' },
	{ if: { swd: 'Low', trep: 'Low', ndvi: 'Good' }, then: 'Suboptimal Season', score: 55, irr: 'Moderate', action: 'Normal procurement but budget for supplementary irrigation costs. Monitor cover crops.' },
	{ if: { swd: 'Optimal', trep: 'Optimal', ndvi: 'Good' }, then: 'Prime Growing Season', score: 80, irr: 'Normal', action: 'Maximize fertilizer procurement! Book peak-harvest logistics and transport capacity early.' },
	{ if: { swd: 'Optimal', trep: 'Optimal', ndvi: 'Vigorous' }, then: 'Excellent Yield Expected', score: 95, irr: 'None', action: 'Outstanding growth projected. Ensure mill capacity is booked. Apply scheduled nutrients fully.' },
	{ if: { swd: 'High', trep: 'High', ndvi: 'Normal' }, then: 'High Rainfall Season', score: 60, irr: 'Monitor', action: 'Expect wet season. Prepare drainage infrastructure. Ensure fertilization avoids heavy rain windows.' },
	{ if: { swd: 'Excess', trep: 'Optimal', ndvi: 'Normal' }, then: 'Heavy Monsoon Expected', score: 40, irr: 'Drainage', action: 'High rainfall period. Prioritize drainage infrastructure clearing. Delay fertilization to prevent leaching.' },
	{ if: { swd: 'Excess', trep: 'Anaerobic', ndvi: 'Stressed' }, then: 'Flood/Leaching Risk', score: 20, irr: 'Critical', action: 'Halt fertilization. Risk of severe Ganoderma spread in wet conditions. Budget for disease management.' }
];

export function condColor(score) {
	if (score < 25) return '#A32D2D';
	if (score < 40) return '#E24B4A';
	if (score < 55) return '#EF9F27';
	if (score < 70) return '#639922';
	return '#3B6D11';
}
export function condBgColor(score) {
	if (score < 40) return '#fef2f2';
	if (score < 55) return '#fffbeb';
	return '#f2f7ec';
}
export function condLabel(score) {
	if (score < 25) return 'Critical';
	if (score < 40) return 'Stressed';
	if (score < 55) return 'Moderate';
	if (score < 70) return 'Good';
	return 'Excellent';
}

export function runDSS(swd, trep, lai, ndvi, isMonthly = false) {
	const activeRules = isMonthly ? SEASONAL_RULES : RULES_DAILY;
	const firings = activeRules
		.map((r) => {
			const s = [];
			if (r.if.swd) s.push(SWD_MF.find((m) => m.name === r.if.swd)?.fn(swd) || 0);
			if (r.if.trep) s.push(TREP_MF.find((m) => m.name === r.if.trep)?.fn(trep) || 0);
			if (r.if.lai) s.push(LAI_MF.find((m) => m.name === r.if.lai)?.fn(lai) || 0);
			if (r.if.ndvi) s.push(NDVI_MF.find((m) => m.name === r.if.ndvi)?.fn(ndvi) || 0);
			return { ...r, strength: Math.min(...s) };
		})
		.sort((a, b) => b.strength - a.strength);

	let wSum = 0;
	let tWeight = 0;
	firings.forEach((f) => {
		if (f.strength > 0.001) {
			wSum += f.strength * f.score;
			tWeight += f.strength;
		}
	});
	const crisp = tWeight > 0 ? wSum / tWeight : 50;
	return { crisp, firings, dom: firings[0] };
}
