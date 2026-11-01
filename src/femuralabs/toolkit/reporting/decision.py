"""Three-way verdict on whether a canditate beats a baseline by a threshold."""
from statistics import mean, stdev

def verdict(base: list[float], cand: list[float], threshold: float) -> str:
	"""Three=way verdict on 'cand beats base by at least threshold'.

	base and cand hold one score per run (one run per seed).
	Higher is better. For lower-is-better metrics, swap the arguments:
	verdict(cand, base, threshold) gives 'baseline minus candidate.'
	as the gain.
	"""

	if len(base) < 2 or len(cand) < 2:
		raise ValueError("need at least two runs per variant.")

	d = mean(cand) - mean(base)
	
	spread = max(stdev(base), stdev(cand))
	low, high = d - 2 * spread, d + 2 * spread
	if low >= threshold:
		return "supported"
	if high < threshold:
		return "not supported"
	return "inconclusive"
