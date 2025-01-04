---
title: Morse code prosigns
date: 2025-01-04
---

It's not technically true that SOS is the universal distress signal in Morse code.

SOS is a sequence of three letters, `... --- ...`, with brief pauses between the letters.

The distress signal is `...---...`, a signal "letter" composed of nine dots and dashes. It's a [prosign](https://en.wikipedia.org/wiki/Prosigns_for_Morse_code), which is sort of like an ASCII control code. Formally, it should be written <span style="text-decoration:overline;">SOS</span>, with an overbar, which means "the dots and dashes for SOS but without pauses".

(Oddly, [this 80's cult classic](https://www.youtube.com/watch?v=0RfU5r63AXY) has backing vocals singing something like `... ---...`, or S<span style="text-decoration:overline;">OS</span>.)

Wikipedia [notes](https://en.wikipedia.org/wiki/SOS) that you can also chop up the distress signal into `...- --.. .`, "VZE", so <span style="text-decoration:overline;">VZE</span> is an equally valid way to write the same prosign.

Ditto <span style="text-decoration:overline;">3B</span>, <span style="text-decoration:overline;">IETMS</span>, and <span style="text-decoration:overline;">EEETTTEEE</span>.

So naturally I wrote some code to find fun equivalent abbreviations for hypothetical prosigns.

There isn't much worth mentioning, algorithmically; just make a hash map with prosigns as keys and words as values, then run through a dictionary and populate it, then sort however you want.

Some fun results:

<span style="text-decoration:overline;">ABSINTHE</span> = <span style="text-decoration:overline;">PHIALS</span>  
<span style="text-decoration:overline;">ACID</span> = <span style="text-decoration:overline;">EMAIL</span>  
<span style="text-decoration:overline;">BEER</span> = <span style="text-decoration:overline;">THIN</span>  
<span style="text-decoration:overline;">BIOLOGY</span> = <span style="text-decoration:overline;">THEOLOGY</span>  
<span style="text-decoration:overline;">BOSS</span> = <span style="text-decoration:overline;">NEWBIE</span>  
<a href="https://en.wikipedia.org/wiki/Time_Cube"><span style="text-decoration:overline;">CUBE</span> = <span style="text-decoration:overline;">TRUTH</span></a>  
<span style="text-decoration:overline;">DADAISM</span> = <span style="text-decoration:overline;">NEWSBEAT</span>  
<span style="text-decoration:overline;">ELECTION</span> = <span style="text-decoration:overline;">FICTION</span>  
<span style="text-decoration:overline;">ENWOVEN</span> = <span style="text-decoration:overline;">LOGIC</span>  
<span style="text-decoration:overline;">HREF</span> = <span style="text-decoration:overline;">SERVE</span>  
<span style="text-decoration:overline;">INTERNET</span> = <span style="text-decoration:overline;">ULTRA</span>  
<span style="text-decoration:overline;">MAINE</span> = <span style="text-decoration:overline;">MAUI</span>  
<span style="text-decoration:overline;">NAMED</span> = <span style="text-decoration:overline;">XML</span>  
<span style="text-decoration:overline;">PERL</span> = <span style="text-decoration:overline;">WILD</span>  
<span style="text-decoration:overline;">WEED</span> = <span style="text-decoration:overline;">WINE</span>  

Inevitably, the best ones were offensive to public morals and basic decency, and have been omitted. Consider it an incentive to write some code yourself.

And yes, some of these pairs have a lot of trivial overlap. Someone should really implement [this algorithm](https://blog.plover.com/lang/anagram-scoring.html) for these things.

Is this the opposite of an anagram? Different letters but in the same order?