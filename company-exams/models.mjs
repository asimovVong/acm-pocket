export function shelfSteps(heights, d) {
  const a = [...heights].sort((x, y) => x-y);
  let right = 0, answer = 1;
  return a.map((value, i) => {
    while (right < a.length && a[right] <= value + d) right++;
    const choices = right - i;
    answer = Number(BigInt(answer) * BigInt(choices) % 998244353n);
    return { a, i, right, choices, answer, value };
  });
}
export function segmentSums(a, cuts) {
  const edges = [0, ...cuts, a.length];
  return edges.slice(0, -1).map((start, i) => a.slice(start, edges[i + 1]).reduce((s, x) => s + x, 0));
}
export function balancedCuts(a, middle) {
  const prefix = [0];
  for (const x of a) prefix.push(prefix.at(-1) + x);
  let left = 1, right = middle + 1;
  while (left + 1 < middle && Math.abs(2*prefix[left+1]-prefix[middle]) <= Math.abs(2*prefix[left]-prefix[middle])) left++;
  while (right + 1 < a.length && Math.abs(2*prefix[right+1]-prefix[middle]-prefix.at(-1)) <= Math.abs(2*prefix[right]-prefix[middle]-prefix.at(-1))) right++;
  return [left, middle, right];
}
