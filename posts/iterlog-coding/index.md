---
title: Iterated log coding
date: 2025-01-01
---

\[\pi = +2^{+2^{+2^{-2^{-2^{+2^{-2^{\cdots}}}}}}}\]

## Floats with just the sign bits

I've created a new format for encoding real numbers on computers. I'm proud of it! Let's dive in.

## Real number formats

We have some real value \(x\in\mathbb R\). Could be positive or negative or zero, large or small. How can we store it in a bitstring?

Fixed-point numbers have one bit for the sign of \(x\) (positive or negative) and \(n-1\) bits for its absolute value \(|x|\), in binary, with an implied decimal point in some fixed location. (They actually usually use two's-complement instead of representing \(|x|\) directly, but let's not get into that right now.)

Floating-point numbers basically use scientific notation. One bit for the sign of \(x\) (positive or negative), some bits for an integer exponent, and some more for the mantissa. This is more flexible because it maintains constant *relative* precision instead of *absolute* precision. Note that the exponent is the floor of the logarithm of the absolute value, \(\lfloor\log |x|\rfloor\), and the mantissa accounts for the fractional part: \(\exp(\log |x| - \lfloor \log |x| \rfloor)\). (I'm using \(\log(a)\) and \(\exp(a)\) to mean \(\log_2(a)\) and \(2^a\), or \(\log_b(a)\) and \(b^a\) if you want to generalize to an arbitrary base.)

[Logarithmic number systems](https://en.wikipedia.org/wiki/Logarithmic_number_system) are similar, but a bit more elegant: instead of separating the integer part of the logarithm from the fractional part and encoding them separately, it's just a direct fixed-point representation of \(\log |x|\) and a separate sign bit for \(x\).

At this point things are getting kind of interesting: we have a sign bit for \(x\) and another (inside the fixed-point representation) for \(\log |x|\). This second sign bit tells us whether the number is large (\(x\ge1\) or \(x\le -1\)) or small (\(-1 < x < 1\)).

[Symmetric level-index](https://en.wikipedia.org/wiki/Symmetric_level-index_arithmetic) representations go farther, and let you represent truly enormous numbers: they encode the number of times you need to take a logarithm to make \(x\) be a reasonable size, as well as what's left over after the final logarithm. Like logarithmic number systems, they have two sign bits, one for \(x\) and one for its *first* logarithm.

But we can do better.

## Introducing the iterated-log format

Let's describe \(x\), a little at a time.

First: is it positive or negative? That's determined by the sign \(s_0 = \text{sgn}\, x\), counting zero as positive. What's left over is the absolute value \(|x|\).

Then: is it large in magnitude or small? Take \(x_1 = \log |x|\) and find its sign, \(s_1 = \text{sgn}\, x_1\). The information left over is \(|x_1|\).

Then: is it very large-or-small, like -10,000 and +0.0001, or just moderately large-or-small, like 1.3 or -0.8? This is determined by \(s_2 = \text{sgn}\, x_2\), where \(x_2 = \log |x_1|\). (To elaborate a bit: we're asking about whether \(x_1 = \log |x|\) is large in magnitude, because very large-or-small numbers have very positive-or-negative logs, i.e. large ones.)

You can see where we go from here. We define \(x_3 = \log |x_2|\) and take its sign \(s_3\). At this point things are getting a bit abstract, but we can still interpret this sign: positive values indicate that \(x\) is extremely large, extremely small, or very close to \(\pm 1\); negative values indicate that it's somewhere in between.

Okay, so what's our proposed format? It's essentially just:

\[s_0s_1s_2s_3\cdots\]

So a small positive number begins \(+-\cdots\), a large negative one begins \(-+\cdots\), etc.

This might not seem like enough information to reconstruct the number, but it is: every additional sign restricts the range of possible values, and any level of precision for a given number can be achieved with enough signs.

## Gray code and lexicographic ordering

Let's stop at three signs' worth of precision for now and see what we have, in order:

```
-++
-+-
---
--+
+-+
+--
++-
+++
```

Well, that's funny! It's a [Gray code](https://en.wikipedia.org/wiki/Gray_code). Cute, but maybe not the most practical.

Let's convert our signs to bits, moving to a standard lexicographic ordering in the process. The rules for this are straightforward:

* For the first bit, \(1\) means positive and \(0\) means negative.
* Every negative sign flips the encoding for subsequent bits

## Rounding and padding

So far, a finite string of sign bits specifies an interval, not a single value.

To fix a well-defined value for every bitstring and handle some annoying fencepost issues, let's specify that:

* An empty sequence of signs represents zero
* If the sign sequence \(S\) represents \(x\), then \(+S\) represents \(2^x\)...
* ...and \(-S\) represents \(-2^x\)
* After converting signs to bits, an extra \(1\) is appended, followed by an arbitrary number of zeroes for padding
* The all-zero bitstring represents `NaN`

This gives us the following values for sequences of up to two signs:
```
-+ [0 0 1] -2
-  [0 1 0] -1
-- [0 1 1] -0.5
   [1 0 0] 0
+- [1 0 1] 0.5
+  [1 1 0] 1
++ [1 1 1] 2
```

## Code

The prototype implementation is in a notebook [here](https://github.com/AdamScherlis/notebooks-python/blob/main/math/iterlog_coding.ipynb), warts and all. There's also some bonus math which I might explain in a later post.

## Every 7-bit number

I know 7 is a weird bit depth, but it's just enough to show off the killer features of this format:

* Lexicographic ordering
* Wide range of values
* Symmetric across zero
* Any value representable in \(n\) bits is representable in \(n+1\) bits
* Numbers too large to represent in any float format
* Numbers too small to represent in any float format
* Numbers extremely close to 1
* Exciting fractally-nonuniform spacing of values
* Wildly unpredictable precision
* etc.

```
[0 0 0 0 0 0 1] -2.004e+19728
[0 0 0 0 0 1 0] -65536
[0 0 0 0 0 1 1] -81.17181
[0 0 0 0 1 0 0] -16
[0 0 0 0 1 0 1] -8.577492
[0 0 0 0 1 1 0] -6.342907
[0 0 0 0 1 1 1] -4.857702
[0 0 0 1 0 0 0] -4
[0 0 0 1 0 0 1] -3.460937
[0 0 0 1 0 1 0] -3.100556
[0 0 0 1 0 1 1] -2.88577
[0 0 0 1 1 0 0] -2.665144
[0 0 0 1 1 0 1] -2.457229
[0 0 0 1 1 1 0] -2.280274
[0 0 0 1 1 1 1] -2.062328
[0 0 1 0 0 0 0] -2
[0 0 1 0 0 0 1] -1.942081
[0 0 1 0 0 1 0] -1.791163
[0 0 1 0 0 1 1] -1.706441
[0 0 1 0 1 0 0] -1.632527
[0 0 1 0 1 0 1] -1.573569
[0 0 1 0 1 1 0] -1.528956
[0 0 1 0 1 1 1] -1.47253
[0 0 1 1 0 0 0] -1.414214
[0 0 1 1 0 0 1] -1.355236
[0 0 1 1 0 1 0] -1.297032
[0 0 1 1 0 1 1] -1.250515
[0 0 1 1 1 0 0] -1.189207
[0 0 1 1 1 0 1] -1.115474
[0 0 1 1 1 1 0] -1.044274
[0 0 1 1 1 1 1] -1.000011
[0 1 0 0 0 0 0] -1
[0 1 0 0 0 0 1] -0.9999894
[0 1 0 0 0 1 0] -0.9576033
[0 1 0 0 0 1 1] -0.8964802
[0 1 0 0 1 0 0] -0.8408964
[0 1 0 0 1 0 1] -0.7996703
[0 1 0 0 1 1 0] -0.7709909
[0 1 0 0 1 1 1] -0.737879
[0 1 0 1 0 0 0] -0.7071068
[0 1 0 1 0 0 1] -0.6791035
[0 1 0 1 0 1 0] -0.6540409
[0 1 0 1 0 1 1] -0.6354978
[0 1 0 1 1 0 0] -0.6125473
[0 1 0 1 1 0 1] -0.5860148
[0 1 0 1 1 1 0] -0.5582966
[0 1 0 1 1 1 1] -0.5149116
[0 1 1 0 0 0 0] -0.5
[0 1 1 0 0 0 1] -0.4848889
[0 1 1 0 0 1 0] -0.4385438
[0 1 1 0 0 1 1] -0.4069625
[0 1 1 0 1 0 0] -0.3752142
[0 1 1 0 1 0 1] -0.3465279
[0 1 1 0 1 1 0] -0.3225228
[0 1 1 0 1 1 1] -0.2889391
[0 1 1 1 0 0 0] -0.25
[0 1 1 1 0 0 1] -0.2058587
[0 1 1 1 0 1 0] -0.1576564
[0 1 1 1 0 1 1] -0.1165842
[0 1 1 1 1 0 0] -0.0625
[0 1 1 1 1 0 1] -0.01231955
[0 1 1 1 1 1 0] -1.525879e-05
[0 1 1 1 1 1 1] -4.99e-19729
[1 0 0 0 0 0 0] 0
[1 0 0 0 0 0 1] 4.99e-19729
[1 0 0 0 0 1 0] 1.525879e-05
[1 0 0 0 0 1 1] 0.01231955
[1 0 0 0 1 0 0] 0.0625
[1 0 0 0 1 0 1] 0.1165842
[1 0 0 0 1 1 0] 0.1576564
[1 0 0 0 1 1 1] 0.2058587
[1 0 0 1 0 0 0] 0.25
[1 0 0 1 0 0 1] 0.2889391
[1 0 0 1 0 1 0] 0.3225228
[1 0 0 1 0 1 1] 0.3465279
[1 0 0 1 1 0 0] 0.3752142
[1 0 0 1 1 0 1] 0.4069625
[1 0 0 1 1 1 0] 0.4385438
[1 0 0 1 1 1 1] 0.4848889
[1 0 1 0 0 0 0] 0.5
[1 0 1 0 0 0 1] 0.5149116
[1 0 1 0 0 1 0] 0.5582966
[1 0 1 0 0 1 1] 0.5860148
[1 0 1 0 1 0 0] 0.6125473
[1 0 1 0 1 0 1] 0.6354978
[1 0 1 0 1 1 0] 0.6540409
[1 0 1 0 1 1 1] 0.6791035
[1 0 1 1 0 0 0] 0.7071068
[1 0 1 1 0 0 1] 0.737879
[1 0 1 1 0 1 0] 0.7709909
[1 0 1 1 0 1 1] 0.7996703
[1 0 1 1 1 0 0] 0.8408964
[1 0 1 1 1 0 1] 0.8964802
[1 0 1 1 1 1 0] 0.9576033
[1 0 1 1 1 1 1] 0.9999894
[1 1 0 0 0 0 0] 1
[1 1 0 0 0 0 1] 1.000011
[1 1 0 0 0 1 0] 1.044274
[1 1 0 0 0 1 1] 1.115474
[1 1 0 0 1 0 0] 1.189207
[1 1 0 0 1 0 1] 1.250515
[1 1 0 0 1 1 0] 1.297032
[1 1 0 0 1 1 1] 1.355236
[1 1 0 1 0 0 0] 1.414214
[1 1 0 1 0 0 1] 1.47253
[1 1 0 1 0 1 0] 1.528956
[1 1 0 1 0 1 1] 1.573569
[1 1 0 1 1 0 0] 1.632527
[1 1 0 1 1 0 1] 1.706441
[1 1 0 1 1 1 0] 1.791163
[1 1 0 1 1 1 1] 1.942081
[1 1 1 0 0 0 0] 2
[1 1 1 0 0 0 1] 2.062328
[1 1 1 0 0 1 0] 2.280274
[1 1 1 0 0 1 1] 2.457229
[1 1 1 0 1 0 0] 2.665144
[1 1 1 0 1 0 1] 2.88577
[1 1 1 0 1 1 0] 3.100556
[1 1 1 0 1 1 1] 3.460937
[1 1 1 1 0 0 0] 4
[1 1 1 1 0 0 1] 4.857702
[1 1 1 1 0 1 0] 6.342907
[1 1 1 1 0 1 1] 8.577492
[1 1 1 1 1 0 0] 16
[1 1 1 1 1 0 1] 81.17181
[1 1 1 1 1 1 0] 65536
[1 1 1 1 1 1 1] 2.004e+19728
```