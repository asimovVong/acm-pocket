"""滴滴 2026-09-06：管材四切。前缀和 + 枚举中间切口 + 双指针。"""
import sys


def min_range(values):
    n = len(values)
    # prefix[t] 是前 t 个数的和；prefix[0] = 0。
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + values[i]

    left = 1
    right = 3
    answer = float('inf')

    # 三个切口满足 1 <= left < middle < right <= n-1。
    for middle in range(2, n - 1):
        # 左半边总和固定，让前两段的差尽量小。
        while left + 1 < middle:
            current_gap = abs(2 * prefix[left] - prefix[middle])
            next_gap = abs(2 * prefix[left + 1] - prefix[middle])
            if next_gap > current_gap:
                break
            left += 1

        # 中间切口右移后，第三段仍必须至少有一个数。
        right = max(right, middle + 1)
        while right + 1 < n:
            current_gap = abs(2 * prefix[right] - prefix[middle] - prefix[n])
            next_gap = abs(2 * prefix[right + 1] - prefix[middle] - prefix[n])
            if next_gap > current_gap:
                break
            right += 1

        first = prefix[left]
        second = prefix[middle] - prefix[left]
        third = prefix[right] - prefix[middle]
        fourth = prefix[n] - prefix[right]
        largest = max(first, second, third, fourth)
        smallest = min(first, second, third, fourth)
        answer = min(answer, largest - smallest)

    return answer


def solve():
    input = sys.stdin.readline
    n = int(input())
    values = list(map(int, sys.stdin.read().split()))
    print(min_range(values))


if __name__ == '__main__':
    solve()
