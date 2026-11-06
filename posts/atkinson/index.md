---
title: The Atkinson and GE indices
date: 2025-03-27
draft: True
--- 

[Previously](https://adam.scherl.is/blog/inequality-metrics) on this blog, I introduced "utilitarian" inequality indices. But I didn't specify what utility function to use.

## Picking a utility function

A feature you might want in an inequality metric is that it gives the same output for the same set of income *numbers*, whether those numbers represent income in dollars, cents, Swiss francs, etc. A metric like this will be invariant under rescaling incomes (multiplying them all by some constant).

I say "a feature you might want" because it is not actually obvious that you *do* want this. The utility function you use is supposed to encode empirical, real-world facts about people's preferences regarding different sums of money (or their welfare, depending on your brand of utilitarianism). There's no law of nature that says that you can't have a sharp cliff at, say, 10,000 USD per year, separating the happy rich from the miserable poor; and this would be meaningfully different from a line drawn at 10,000 cents or 10,000 francs.

On the other hand, every major currency is a fiat currency. If you magically replaced every dollar in the world with a cent, then (assuming the resulting panic and confusion didn't destroy civilization) Econ 101 predicts that prices, wages, etc. would soon drop by a factor of 100 and life would continue otherwise unchanged. For that matter, it seems pretty likely that differences in purchasing power would cause any purported utility cliff to appear in different places (in real terms) in different countries. So any inequality metric that aims to be universal -- to apply regardless of inflation and purchasing-power differences and so on -- has to be invariant under rescaling.

The only utility function that's invariant under rescaling the input is a constant one. But if you just want the utility function to be *equivalent* after rescaling, then you can take advantage of the fact that (positive) linear transformations of utility don't affect anything meaningful. In particular, the \(a\)-metric defined in the previous post is invariant to this.

Which functions are there for which rescaling the input \(x\) is equivalent to some linear transformation of output? As it [turns out](https://en.wikipedia.org/wiki/Cauchy%27s_functional_equation), there are three cases (up to linear transformations):

* Power laws of the form \(x^\alpha\) for some \(\alpha\)
* Logarithmic functions like \(\log x\)
* Pathological space-filling functions (assuming the axiom of choice)

We can rule out the third on various grounds, such as that they're not continuous, not monotonic, offensive to common sense and decency, or that an example of one can never be constructed explicitly.

We can unify the other two cases by noting that if you apply a linear transformation to get \(\frac1\alpha x^\alpha - \frac1\alpha\) and take the limit \(\alpha\to 0\), you get \(\log x\).

For this reason, these two cases are usually referred to as "the" Atkinson index and controlled by a single parameter \(\epsilon=1-\alpha\).

The corresponding \(b\)-index is the "generalized entropy index" with parameter \(\alpha\).

## Empirical evidence for logarithmic utility of money

## Test cases for Atkinson

## Empirical results for Atkinson vs Gini

## Aggregation

sketch it out
do the math if necessary

## Impossible utility functions

The generalized entropy index is sometimes used with \(\alpha=2\), in which case it's equivalent to the variance of the income distribution. (For example, Wikipedia's article on the generalized entropy index is illustrated with a heatmap of GE(2) for South Africa.)

This seems superficially fine -- it goes up with inequality is worse and is a special case of the scale-invariance utilitarian metrics defined above.

But consider the corresponding utility function. It's a quadratic function whose leading term is negative, or in graphical terms, an upside-down parabola. The utility initially grows with income, with diminishing returns; but then the returns diminish until utility has passed its peak and is actually decreasing with additional income.

So this is an absurd metric that gives halfway-reasonable results.

## Inequality and sparsity

Hoyer ratio

whatever the thing was about integrating some other thing to get Hoyer ratio

arggggh where are the notessss