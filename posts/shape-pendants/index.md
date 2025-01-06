---
title: Procedurally-generated shapes for laser-cut pendants
date: 2025-01-05
---

I handed out laser-cut pendants this past Burning Man that looked like this:

![wooden pendants in a variety of symmetrical jagged shapes](../assets/shape-pendants/pendants.jpg)

I made fifty of them, each a unique shape, with rotational symmetry of varying orders.

## Shapes

My desiderata were approximately:

* Unique shapes
* Vaguely circular
* Lots of random detail
* Somewhat symmetric
* Smooth enough for the laser cutter to handle

Describing the shapes in polar coordinates and taking a Fourier series made it pretty easy to get all of this.

We can make the function periodic with period \(2\pi\) (for a closed shape) or \(2\pi/N\) (for \(N\)-fold rotational symmetry) by limiting the frequencies in the series to multiples of \(1\) or \(N\) (respectively).

The shape of the amplitude spectrum controls the general vibe of the shapes, and the phases determine all the details. Fractals and many kind of natural textures have power-law spectra, so I used that for the amplitudes and generated the phases \(\phi_k \sim U(0, 2\pi)\) uniformly randomly:

\[r(\theta) = r_0 + \sum_{k=1}^{k_{\text{max}}} (kN)^{-\alpha} \cos(kN\theta + \phi_k) \]

Then I fiddled with the hyperparameters (power-law exponent \(\alpha\), highest frequency \(k_\text{max}N\) before the smoothness cutoff, constant term \(r_0\), order \(N\) of rotational symmetry) until I liked the batches of shapes coming out of my script.

## Cutting

Most laser cutters at hackerspaces seem to be hooked up to computers running LightBurn, which is pretty similar in interface to Inkscape or Adobe Illustrator. It imports SVG seamlessly (often with distance units and layers intact), so I try to keep my workflow inside Python as much as possible, then in Inkscape for any touch-ups or manual steps, and then in LightBurn to set details of cuts and engraving and any last-minute issues I forgot.

For this project, I added the Burning Man logos in Inkscape. Just before the cut, my friend Cody suggested giving them holes for necklaces or keychains, which I added in LightBurn. In hindsight, I wish I'd done both of those in Python, with the hole position chosen automatically. 

The aftermath: 

![wooden square with jagged symmetrical shapes cut out, with laser cutter visible in background](../assets/shape-pendants/pendants-cut.jpg)

## Ephemerality?

The photo at the top of the post is apparently the only decent one I took. You'll have to trust me that the pile of fifty pendants looked cool; fifty different people have them now.

## Code

My Jupyter notebook is [here](https://github.com/AdamScherlis/notebooks-python/blob/main/lasers/tokens/tokens.ipynb).

Most of the hard-coded "magic numbers" are things I just fiddled with repeatedly until things looked right.