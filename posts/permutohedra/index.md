---
title: A factorial puzzle
date: 2025-02-25
---

## Problem

I saw [this post](https://math.stackexchange.com/questions/5038292/a-factorial-puzzle) on Math Stack Exchange recently. Unfortunately, it got closed while I was solving it, so I emailed the OP a summary and am writing it up here.

In the course of some representation theory research, OP came across a mysterious function that produces, for each \(n\in\mathbb{N}\), a set of \((n-1)\)-tuples of natural numbers of size \(n!\). They give some fairly gnarly Mathematica code to compute it, and ask for a simple characterization. They also list the sets for \(n=1,2,\dots,5\).

So there's actually three very different puzzles here, with the same answer. In increasing order of sophistication:

1. Stare at the given sets until the pattern becomes clear.
2. Reverse-engineer and golf the Mathematica code.
3. Solve the original representation-theory problem.

I'm not feeling sophisticated, so we're going to do the first one.

## Clues

There are a couple observations we can make about the given example sets:

1. Per OP, they each consist of the vertices of a convex polytope which is combinatorially equivalent to the [permutohedron](https://en.wikipedia.org/wiki/Permutohedron).
2. The edges of each polytope have coordinates that are all zero or one (in one orientation).

As a reminder, the standard \((n-1)\)-dimensional permutohedron is the convex hull of the \(n!\) permutations of the vector \([1,2,\dots,n]\). (These lie in a hyperplane of codimension \(1\) in \(\mathbb{R}^n\).)

In other words, the vertices of the permutohedron are linear combinations of standard basis vectors, with the coefficients of each vector being a permutation of \((1,2,\dots,n)\).

## Guess

We will wildly conjecture that our mystery function gives a linear transformation of the standard permutohedron. Therefore, its vertices should be linearly combinations of some unknown set of vectors in \(\mathbb{R}^{n-1}\), with the coefficients again being a permutation of \((1,2,\dots,n)\).

What do we know about these vectors?

Consider the standard permutohedron again: every edge is a permutation of the vector \([+1, -1, 0, \dots, 0]\), which is a difference of two standard basis vectors. These are also the edges of the \((n-1)\)-simplex formed by the standard basis vectors.

We know that the edges of our polytope are zero-one vectors, which is to say, edges and diagonals of the unit \((n-1)\)-cube. So it would make sense if the unknown vectors are the vertices of some \((n-1)\)-simplex embedded in that cube.

A little bit of squinting at the first few sets reveals that this *almost* works, for the simplex with vertices e.g. \([0, 0, 0], [0, 0, 1], [0, 1, 1], [1, 1, 1]\). It gives the correct shape, but translated away from the origin.

How do we translate back? Note that there is always one vertex of our polytope which is at least as close to the origin as any other corner along all axes simultaneously. This is the vertex whose coefficients are \((n,\dots,2,1)\) in decreasing order. The coordinates of that vertex are cumulative sums of the coefficients, i.e. triangle numbers.

So the polytope is just a permutohedron "jammed into the corner" of the positive orthant by a linear transformation, with coordinates given by cumulative sums of permutations with triangle numbers subtracted.

## Solution

In equations:

The mystery set for \(n\) is given by the \(n!\) vectors \(w^\sigma\) for \(\sigma\in S_n\) with components given by
\[w^\sigma_j = \sum_{i=1}^{j-1}(\sigma(i) - i) \qquad i\in[1..n],j\in[1..(n-1)]\]

In Python:

```py
import numpy as np
from itertools import permutations

for perm in permutations(range(n)):
    print(np.cumsum(np.array(perm) - np.arange(n))[:-1])
```