"""滴滴 2026-09-06：层板限差。排列按从下往上的顺序理解。"""
import sys

MOD = 998244353


def count_arrangements(heights, d):
    a = sorted(heights)
    n = len(a)
    answer = 1
    right = 0

    for i in range(n):
        # right 最终停在第一个大于 a[i] + d 的位置；可以等于 n。
        while right < n and a[right] <= a[i] + d:
            right += 1

        # 假想从高到矮插入 a[i]：
        # 能接在 a[i] 前面的较高箱子有 right-i-1 个，
        # 再加上放到整个排列开头这 1 种位置，共 right-i 种。
        choices = right - i
        answer = answer * choices % MOD

    return answer


def solve():
    input = sys.stdin.readline
    n, d = map(int, input().split())
    heights = list(map(int, sys.stdin.read().split()))
    print(count_arrangements(heights, d))


if __name__ == '__main__':
    solve()
