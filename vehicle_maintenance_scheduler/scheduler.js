function scheduleTasks(tasks, maxHours) {
  const n = tasks.length;
  const dp = Array(n + 1)
    .fill()
    .map(() => Array(maxHours + 1).fill(0));
  for (let i = 1; i <= n; i++) {
    for (let w = 0; w <= maxHours; w++) {
      if (tasks[i - 1].duration <= w) {
        dp[i][w] = Math.max(
          tasks[i - 1].impact + dp[i - 1][w - tasks[i - 1].duration],
          dp[i - 1][w]
        );
      } else {
        dp[i][w] = dp[i - 1][w];
      }
    }
  }
  return dp[n][maxHours];
}
module.exports = { scheduleTasks };