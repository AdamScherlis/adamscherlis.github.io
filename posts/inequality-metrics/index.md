---
title: Utilitarian inequality metrics
date: 2025-11-11
--- 

TL;DR: Use Atkinson with \(\epsilon = 1\) or generalized entropy with \(\alpha=0\).

Inequality indices are numerical metrics of income (or wealth, etc) inequality.

There are some downsides to society coordinating around a few canonical numerical metrics, like [Goodhart's law](https://en.wikipedia.org/wiki/Goodhart%27s_law); there are also big upsides, like making it harder to cherry-pick statistics, and staying grounded in something reality-based rather than making policy based on vibes.

But if you're *going* to coordinate on a metric, you should pick a good one!

Inequality comes in many forms. Even sticking to income inequality, there's an infinite-dimensional space of income spectra; a "moderately unequal" society might be one with a broad bell-curve of income centered at a typical value, or a narrow distribution plus a long tail of billionaires, or a bimodal distribution with two distinct clusters, etc.

An inequality metric collapses this variety down to a single number. In the process, it inevitably makes strong assumptions about *how bad* it thinks different kinds of inequality are. If the metric is designed haphazardly, those assumptions might be very far from reasonable! Worse, the people using the metric may have very little intuitive of sense of what those assumptions *are*. A good metric should make good tradeoffs, but at the very least you should know which tradeoffs you're making.

I think the most popular indices (especially Gini) make bad assumptions, and some others -- notably the Atkinson and generalized-entropy metrics -- make assumptions that are about as good as we could hope for.

In this post I argue for a somewhat broader class of inequality metrics, which I call "utilitarian". In a future post I'll argue for the Atkinson and GE indices in particular.

## Why not Gini?

The Gini coefficient is *far and away* the most popular income-inequality metric; if only one metric is reported in a given context, it's almost always [Gini](https://en.wikipedia.org/wiki/Gini_coefficient).

Pros: Gini is fairly easy to calculate, and you can draw a nice diagram to explain how it's defined. It also satisfies the most basic desiderata of an income inequality metric: in particular, it always decreases when money is transferred from higher to lower incomes, is zero for perfect equality, and does not depend on the currency unit you use to measure income.

Cons: The Gini coefficient was designed to be easy to explain with a nice diagram, which unfortunately has nothing to do with weighting different kinds of inequality against each other.

As a consequence, I think it makes bad tradeoffs. The following countries have Gini coefficients of 0.1:

* In Country A, ~89% of people have the same income and ~11% make 1/10 that income. 
* In Country A', 90% of people have the same income and 10% are completely destitute.
* In Country B, ~99% of people have the same income, while the top ~1.2% have 10× that income.
* In Country B', nearly all people have the same income, while one person has 10% of the total income of the entire country.
* In Country C, 50% of people have the same income, and the other 50% have 1.5× that income.

By my lights, B' seems far worse than B, and A' seems far worse than A. Also, both A' and B' seem much worse than C.

The comparison of A vs. B (or A' vs. B') is to some extent a matter of what effect you're trying to measure; if you're more concerned about plutocracy vs. extreme poverty, you might make different tradeoffs.

On the other hand, I think Gini fails to measure different levels of poverty in any reasonable way; zero income is much worse than low income, especially if we're defining income to include government programs. The Gini coefficient completely loses sensitivity in this limit, and starts to depend only on the number of low-income people, but not on how much income they actually have.

It also fails to measure extreme income concentration reasonably, losing sensitivity (in the limit) to the degree of concentration (the number of high-income people) and depending only on their total income.

Whether or not you agree with the utilitarian arguments I make in this post, I think you should be using utilitarian inequality metrics. The fact that they can be derived from *any* reasonable philosophical position gives them a sort of groundedness and robustness that I think other metrics lack.

And whether or not you agree with *that*, I think you should cook up some hypothetical countries before using any metric! For anything! Get a gut-level sense of what 0.1 or 0.3 or 0.99 might mean in practice.

## Utilitarian inequality metrics

I think trying to capture the effects of (relative) poverty and the effects of a few outlier super-wealthy individuals in the same metric is basically a mistake. Also, none of them do it. People who are concerned about plutocracy usually point to individuals like Elon Musk and Jeff Bezos, who have incomes on the order of 10 to 100 billion dollars. That's definitely a lot of money; I think it's reasonable to worry about how much power this gives a small number of people. It's also less than 0.4% of the total income of all Americans. It affects the Gini coefficient of the US by less than 0.004. (The number for wealth is similar.)

Instead, I think it's better to focus on what inequality metrics are good at: capturing the intuition that unevenly-distributed resources leave people worse off in an overall sense.

There's a very clean utilitarian case against economic inequality, which I think captures this pretty well:

* People have diminishing marginal utility of money (and most other resources): an addition $1,000 changes your life a lot more if you're making $10k rather than $100k.
* Therefore, giving additional marginal resources to people who already have more leads to less total utility than giving it to people who have less.
* More formally: utility functions are concave and Jensen's inequality applies.

I don't think this simple model captures everything that's bad about inequality; income disparities have some bad externalities. But I do think it captures *most* of it.

It also leads directly to a class of inequality metrics that are fairly easy to define and calculate, and which can be adjust to fit any utility function. Given a function \(U\) and a mean income \(\mu\) we can define two metrics:

\(a = 1 - U^{-1}(\mathbf E_y[U(y)]) / \mu\)

\(b = U(\mu) - \mathbf E_y[U(y)]\)

where \(y\) is the income of an individual and \(\mathbf E_y\) is the average over all individuals.

The \(a\)-index measures the fraction of total income that is wasted (in a utilitarian sense) due to inequality. If \(a = 0.25\), then a perfectly-equal society with 75% of the total income is judged by your utility function to be just as good as the actual one.

The \(b\)-index measures the loss to average utility due to inequality, directly in "utils". Depending on your utility function this may have additional interpretations.

The Atkinson index is a family of indices which corresponds to \(a\) for power-law and logarithmic utility functions. Generalized entropy indices are the corresponding \(b\)-indices.

These indices have been discovered multiple times, mostly by people who didn't have utility functions in mind at all; I think they have a mathematical elegance (and some nice practical properties) that make them appealing even without any of the utilitarian motivation.

I think logarithmic utility is the best-supported model, but that's a story for a future post. (This gives you metrics that are functions of the geometric mean of income.)

### Aside: the veil of ignorance

The Rawlsian "veil of ignorance" argument, contrary to the above, suggests that we should focus entirely on maximizing the welfare of the worst-off in society, and that the relative (or absolute!) welfare among everyone else simply doesn't matter in comparison.

It also assumes that someone behind the veil would be infinitely risk-averse. I don't know about you, but given the choice between being born into:

* Country A, where half the population lives on $1/day and the other half lives on $200/day
* Country B, where one person lives on $0.99/day and everyone else lives on $100/day

I would have a strong preference for B. Moral considerations aside, thinking only of my own wellbeing (as Rawls assumes), I am perfectly willing to risk a slightly worse bad outcome if I can nearly eliminate the risk of that outcome.

Apparently John Harsanyi made a similar argument, almost 20 years before Rawls, and arrived at a conclusion in support of utilitarianism.

## Tradeoffs

Holding inequality constant, it is good for the average person to be wealthier. As a society, we should be trying to increase abundance to some extent, and trying to decrease inequality to some extent. These trade off against each other. (I'm not claiming current policy is Pareto-efficient!)

Utilitarian inequality metrics suggest a particular set of tradeoffs: those that maximize average (or total) utility. This can be translated directly into a rate at which the metric trades off against average income. So if we take them literally, these metrics make policy recommendations that extend beyond inequality itself.

As I noted above, however, these metrics don't capture the full impact of inequality. You could try to incorporate that by making different tradeoffs which weight inequality more strongly. (There's an upper bound here: a policy that makes everyone worse off, but affects the rich the most, is still not a very good policy.)

You might also have other, non-utilitarian constraints on which policies you'll favor, or even consider. Personally I think making policymaking a bit more utilitarian would be a big improvement over the status quo; you might have very different views.

So I'll retreat to a weaker demand: if you're going to use an inequality metric at all, make it a utilitarian one -- even if you're not a utilitarian.