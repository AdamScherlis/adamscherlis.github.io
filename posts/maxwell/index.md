---
title: Maxwell's Demon and the Arrow of Time
date: 2025-11-04
---

(Loosely based on a recent conversation with a housemate)

SIMPLICIO: So, I really don't get why Maxwell's demon is supposed to be impossible. Why can't I just attach a wheel to a ratchet, stick it in a gas that's in thermal equilibrium, and wait for a random fluctuation to turn it? It'll keep turning in one direction, and I should be able to harness that to extract at least a little bit of power.

SALVIATI: As it turns out, you can't really build a ratchet at microscopic scale!

SIMPLICIO: No, I mean a macroscopic one.

SALVIATI: Ah. Well, then it's going to take a really big, unlikely fluctuation to create enough of a gust to turn it -- a thermodynamic miracle.

SIMPLICIO: I'm a patient man.

SALVIATI: My next objection is that even a macroscopic ratchet won't be ideal. Let's be concrete. How does your ratchet work?

SIMPLICIO: A wheel with sawtooth teeth, pressed against a spring-loaded pin, like in a ratchet strap.

SALVIATI: And when you turn the wheel one tooth, the pin snaps back down into place to block it?

SIMPLICIO: Exactly.

SALVIATI: Then you have two options. Either the mechanism is frictionless -- in which case the pin, once set in motion, will bounce around forever and never settle down enough to block the tooth -- or it has friction, which dissipates the pin's kinetic energy as heat. But in that case, we need to model the ratchet's constituent atoms, not just its macroscopic parts.

SIMPLICIO: Can't we just treat friction as an unexamined fundamental force?

SALVIATI: Only if you want to break conservation of energy. If the kinetic energy is lost to "friction", and not just transformed into another kind of energy, then all the energy in the gas will eventually leak out through the ratchet.

SIMPLICIO: Okay, so my ratchet is made of atoms. Why is this a problem?

SALVIATI: They'll be in thermal equilibrium with the gas, so they're vibrating around a bunch. Once in a great while, the pin will get jostled by this, hard enough to push the spring back and allow the ratchet to move the wrong way.

SIMPLICIO: Surely that won't happen as often as the gusts that turn it the right way!

SALVIATI: Remember that the gusts of wind are exponentially unlikely; every molecule that participates in them lowers the odds by an additional multiplicative factor.

SIMPLICIO: Okay, I'll grant that both processes are comparably rare. It still seems like a strange coincidence that the miraculous gusts and the miraculous jostles should happen at exactly the same rate. They seem unrelated.

SALVIATI: I think they have to match up. Systems in thermal equilibrium don't have an arrow of time -- any process has to happen equally often in both directions. That includes the wheel turning one way or another.

SIMPLICIO: I believe you, but that's pretty abstract. Is there a more mechanistic explanation, for the specific case of the ratchet? Some way to connect the jostles to the gusts?

SALVIATI: Let's see. It's not just the macroscopic behavior that's reversible in equilibrium. Things will happen equally often in forward and reverse at a microscopic level. Let's imagine that we can take a detailed video of everything that happens when the wheel turns the correct way, from miracle-gust to heat dissipation, at a molecular level. When I play this video backwards, it should look just like a typical example of the wheel turning the wrong way. Instead of heat dissipating through the mechanism at the end, random molecular movements at the beginning happen to conspire to concentrate energy near the pin. Then, instead of the pin being slowed by friction in the mechanism, the mechanism sort of twitches and throws the pin into motion. That allows the wheel to turn -- we only need it to turn a tiny bit, to place the pin on top of a tooth, so this doesn't require much 'miracle juice'. The spring pushes the pin down the sloped side of the tooth, the wheel turns harder, and then just as the pin reaches the bottom of the slope, the wheel's kinetic energy gets transferred to the gas, creating a brief gust of wind that quickly dissipates. You can see how that's the same as the gust driving the wheel, just in reverse. So the time-reversed version of a miraculous fluctuation is just an ordinary dissipative process. 

SIMPLICIO: Is, um, miracle juice a real thing? Can we compare the amount of miracle juice needed for the forward and reverse videos?

SALVIATI: Hmmm. Yes, it is! Let's pretend I had something concrete in mind, like the log-probability of the miraculous process. That's going to correspond exactly to the decrease in entropy that happens at the 'miraculous' step, either to create a gust or to jostle the pin. Entropy stays constant during the main operation of the ratchet -- from jostle to gust, or vice versa -- and then increases when the dissipative step happens at the end, either from friction or from the final gust mixing with the gas.

SIMPLICIO: I feel like we're just sweeping my confusion about the equal-probability coincidence under a big rug labeled ENTROPY. Why is the entropy decrease the same for the jostle miracle and the gust miracle?

SALVIATI: I think the best I can do there is to connect it to energy. In both cases, the miracle involves a concentration of energy into a few degrees of freedom. Those degrees of freedom -- the gust, or the jostling part of the mechanism -- won't have much entropy; there's very few microstates in that macrostate. In other words, the macroscopic description pins down the microscopic motion pretty well. But now every other degree of freedom, for all the other gas molecules and ratchet atoms in the system, is deprived of that energy. This constrains their motion a bit, makes them a little less unpredictable; you end up with fewer microstates per macrostate -- less entropy.

SIMPLICIO: Is there some law relating the amount of energy concentration to the amount of change in entropy?

SALVIATI: The ratio between them is usually called "temperature".

SIMPLICIO: That feels a bit like a magic trick, but I'm relieved that we can ground it out in terms of energy. That at least makes sense: kinetic energy gets concentrated into one big gust of air, then pushed into the wheel, the spring, the pin, and finally into the mechanism as heat. And what you're saying is that when the ratchet slips back the wrong way, the same amount of energy is flowing in the reverse order.

SALVIATI: Precisely!

SIMPLICIO: There's still something here that seems unsatisfying. Let's see. Okay, at some time \(t\), I observe the wheel turning the wrong way. What you're saying is that I should hypothesize a recent, miraculous event that jostled the pin out of the way. Something feels fishy about invoking a miracle like that.

SALVIATI: That probably should feel fishy. You have a strong sense of what kinds of physical processes are common, and which aren't; but that intuition is grounded in everyday life, where entropy is always increasing. Thermal equilibrium is very different. Entropy is nearly always near its maximum value, with occasional downward fluctuations. When you see something low-entropy happening, the best guess for its future behavior is that entropy will increase back towards the maximum -- that's no different from everyday life. But the best guess for its past behavior is that entropy was steadily decreasing until just a moment ago! That's the hypothesis that requires the smallest downward fluctuation, and the smallest miracle.

SIMPLICIO: Okay, let me see what that means in practice. Suppose I observe an egg at rest, a meter above the floor. My best guess -- in normal life, or in equilibrium -- is that it's about to fall and break. But what you're saying is that, if this observation was sampled from a system in equilibrium, the best guess for its recent behavior is that it was lying on the floor, smashed, only to spontaneously fix itself and leap into the air.

SALVIATI: Correct!

SIMPLICIO: But -- hold on. "Thermal equilibrium" is pretty close to a uniform distribution over microstates, right?

SALVIATI: Yes, plus a constraint on total energy. Modulo some handwaving about microcanonical and canonical ensembles...

SIMPLICIO: That seems like a decent Bayesian prior. Why doesn't this argument apply to the actual past? Entropy seems to be low now, but why should we hypothesize that it was even lower in the past? Maybe this very moment is the most ordered moment in history, and the real history of the world looks like a video played in reverse! One year ago it was 2026, and I was a year older -- and one year from now it'll be 2026 again!

SALVIATI: That's the Boltzmann paradox! Honestly, I think the best argument against it is just that it produces absurd results. The universe started in a low-entropy state; we don't really know why, but the hypothesis seems to be necessary.

SIMPLICIO: What do we actually know about the initial state of the universe?

SALVIATI: Based on normal Big Bang cosmology, it was at some point much smaller, in a hot, dense state -- and also, I might add, an extremely flat and smooth state. Suspiciously so, some might say.

SIMPLICIO: Do we know how it got so flat and smooth? Or is that where we have to appeal to "things were really low-entropy" as a kind of deus ex machina?

SALVIATI: That's what cosmic inflation is supposed to explain. It hypothesizes an early stage of very rapid exponential expansion. It seems to hold together as a theory -- although some people object to the initial conditions required. See, you need to start out with nearly all of the universe's energy concentrated into potential energy for a quantum field, and if you try to quantify how 'fine-tuned' or 'special' that state is, it's even more special than the flat, smooth state after inflation.

SIMPLICIO: Er. Is that just saying that entropy increases during the inflation step?

SALVIATI: According to a talk at a conference I once attended, yes. But the Q&A session afterwards was extremely loud and confusing.

SIMPLICIO: How are we supposed to judge any theory about the past if "entropy increased" is a necessary hypothesis and also requires fine-tuning the initial conditions?

SALVIATI: I think that's where I take issue with something you said earlier, about Bayesian priors. I think the uniform distribution must be a pretty bad prior after all, and we should be using something closer to a Solomonoff prior. I don't think it's a problem to posit a very low-entropy initial condition, as long as it's also a very simple one in some computational sense.

SIMPLICIO: So you've reduced a confusing conceptual problem to a provably uncomputable one.

SALVIATI: Yes! And now it's not my fault that I don't know the right answer.