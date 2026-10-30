"""
Big-O Asymptotic Complexity Models and Inference Rules.
"""

from __future__ import annotations
from typing import List, Optional


class BigO:
    O_1 = "O(1)"
    O_LOG_N = "O(log N)"
    O_N = "O(N)"
    O_N_LOG_N = "O(N log N)"
    O_N2 = "O(N^2)"
    O_N3 = "O(N^3)"
    O_2N = "O(2^N)"
    O_N_BANG = "O(N!)"

    # Hierarchy ranking for taking asymptotic bounds max(A, B)
    RANK = {
        O_1: 1,
        O_LOG_N: 2,
        O_N: 3,
        O_N_LOG_N: 4,
        O_N2: 5,
        O_N3: 6,
        O_2N: 7,
        O_N_BANG: 8,
    }

    @classmethod
    def max_complexity(cls, c1: str, c2: str) -> str:
        r1 = cls.RANK.get(c1, 1)
        r2 = cls.RANK.get(c2, 1)
        return c1 if r1 >= r2 else c2

    @classmethod
    def aggregate(cls, complexities: List[str]) -> str:
        if not complexities:
            return cls.O_1
        highest = cls.O_1
        for c in complexities:
            highest = cls.max_complexity(highest, c)
        return highest

    @classmethod
    def infer_from_loops_and_recursion(
        cls,
        max_loop_depth: int,
        has_recursion: bool,
        recursion_branching: int,
        has_logarithmic_step: bool = False,
        has_sort: bool = False,
    ) -> str:
        """
        Determines the estimated Big-O time complexity based on structural features.
        """
        if has_recursion:
            if recursion_branching >= 2:
                # Tree-shaped recursion without memoization (e.g. fib(n-1) + fib(n-2))
                return cls.O_2N
            elif recursion_branching == 1:
                if has_logarithmic_step:
                    return cls.O_LOG_N
                return cls.O_N

        if max_loop_depth >= 3:
            return cls.O_N3
        elif max_loop_depth == 2:
            return cls.O_N2
        elif max_loop_depth == 1:
            if has_logarithmic_step:
                return cls.O_LOG_N
            return cls.O_N
        elif has_sort:
            return cls.O_N_LOG_N

        return cls.O_1

    @classmethod
    def infer_space_complexity(
        cls,
        has_recursion: bool,
        recursion_branching: int,
        allocates_collection: bool = False,
        allocates_matrix: bool = False,
    ) -> str:
        """
        Infers space complexity based on recursion depth and allocation.
        """
        if allocates_matrix:
            return cls.O_N2
        if allocates_collection:
            return cls.O_N
        if has_recursion:
            # Call stack frames
            return cls.O_N
        return cls.O_1
