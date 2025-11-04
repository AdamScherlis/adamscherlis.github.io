---
title: Rainbows, fractals, and crumpled paper: H&ouml;lder continuity
date: 2025-11-03
---

One of my favorite website is [allRGB](https://allrgb.com/). It's a collection of images which each contain every 24-bit RGB color exactly once. Most of them (though not all) are square 4096-by-4096 images. (In general, we can imagine doing this with \(n^2\)-level color for any \(n\), producing \(n^3\times n^3\) images; allRGB is the case \(n=16\).)

People take that prompt in a ton of different directions; many of the images use clever dithering tricks to simulate a smaller color palette, others arrange their pixels into tiny regions of similar color, etc. But I think my favorites are the ones that attempt to arrange colors as *smoothly* as possible, like [Order from Chaos](https://allrgb.com/order-from-chaos) or [Smooth](https://allrgb.com/smooth).

(Many of the images look smoother than they are, because of small-scale dithering or stripes or similar -- you have to zoom in to see the actual grain.)

How smooth can these images get? To be more precise: what's the smallest \(C\) such that there exists a bijection \(f: [n^3]^2 \to [n^2]^3\) for which \(|f(x)-f(y)| \le C\) for all \(x,y\) such that \(|x-y|=1\)?

(Or, probably better: what is the smallest \(C\) such that \(|f(x)-f(y)| \le C |x-y| \forall x,y\)? This is equivalent if we use the Manhattan metric and is the discrete version of Lipschitz continuity.)

We can also think of this problem in a different guise: given a (discretized) square of paper, we want to crumple it up into a (discretized) cube such that it fills the cube uniformly and is stretched out as little as possible in the process.

If we use Euclidean distance in both image space and color space, then we can rule out \(C=1\) with some casework (which I have misplaced, so you'll have to trust me). The allrgb image called "Smooth" achieves \(C=2\) in a way that looks likely to generalize, so the only remaining question is whether \(C=\sqrt 2\) is possible.

Of course, this problem also generalizes to maps between \(a\)- and \(b\)-dimensional space, i.e. \([n^a]^b \to [n^b]^a\), for any \(a > b\). (We can also ask about \(a < b\), which includes the case of trying to make allRGB images smooth in the inverse sense -- keeping similar colors as close together as possible. It's not too hard to show that in this case we have to accept pretty large discontinuities.)

Starting with the simplest nontrivial case, \((a,b) = (2,1)\), we are presented with the challenge of trying to smoothly biject a line onto a square. This is extremely easy in the discrete setting we're working in: just weave back and forth in rows, boustrophedon-style.

But it feels like something's missing from this approach -- or even that of "Smooth" -- compared to, say, "Order from Chaos". You can imagine taking \(n\to\infty\) and turning the latter into a nice continuous map from \([0, 1]^2 \to [0, 1]^3\) by progressively adding more detail; if you try that with the alternating-rows map, it fails to converge. If you try it with "Smooth", the \(8\times 8\) grid of lines turns into an \(\frac n2 \times \frac n2\) grid, which also fails to converge.

As it turns out there's a very beautiful solution to this for the \((2,1)\) case, called the [Hilbert curve](https://en.wikipedia.org/wiki/Hilbert_curve). It's an example of a space-filling curve, that is, a continuous, surjective map from the interval to the square. In other words, it's a fractal curve with fractal dimension 2. (It's not injective, and no space-filling curve can be injective, but I think it only fails this mildly; in particular there's a finite number of preimages for each point on the square, unless I'm mistaken.) [xkcd] famously used this to map out IP address space graphically.

How continuous are these maps? The obvious generalization of our definition of smoothness above gives Lipschitz continuity, i.e. \(|f(x)-f(y)| \le C |x-y|\) for some \(C\); this would mean that our map "stretches out" the interval by a finite amount \(C\). But (exercise for the reader) this is impossible.

On the other hand, continuity alone is pretty weak; we can do better.

The Hilbert curve has the nice property that a interval of length \(r\) of the unit interval gets mapped to a reasonably compact region of area \(r\) in the square, which has a diameter on the order of \(\sqrt r\). This implies the property  \(|f(x)-f(y)| \le C |x-y|^{1/2}\), which is called H&ouml;lder continuity (with exponent 1/2).

Can we use space-filling curves to construct H&ouml;lder-continuous versions of our allRGB images? Not directly. You can chain together Hilbert-curve maps to go down from 2 dimensions to 1 and then back up to 3, but the [gorgeous result](https://allrgb.com/hilbert-curve) is discontinuous everywhere. (You can also do this with [a Z-order curve](https://allrgb.com/z), which has a particularly simple algorithm -- just interleave and deinterleave the bits of your coordinates to get your color components.)

As it turns out, this question [has been asked](https://mathoverflow.net/questions/204007/best-h%C3%B6lder-exponents-of-surjective-maps-from-the-unit-square-to-the-unit-cube) before! The accepted answer links to two great papers on the subject. The [first](https://link.springer.com/article/10.1007/PL00009375), by R. Stong, uses a clever fractal construction to solve the problem for \(\mathbb Z^a \to \mathbb Z^b\). The [second](https://arxiv.org/abs/math/0302308) shows (very nonconstructively) that this implies a map \(\mathbb R^a \to \mathbb R^b\); I think you can make this much more constructive, though, by taking advantage of the fractal nature of Stong's construction. (In the \((3,2)\) case, we construct a fractal curve with fractal dimension \(3/2\) in the plane, then map two of these Lipschitz-continuously to 3D space.)

Unfortunately, as far as I can tell, this construction on \(\mathbb R^a \to \mathbb R^b\) does not restrict to a bijection between hypercubes; it zigzags around too much to be able to cut out a contiguous chunk like that. So some version of this problem remains open.