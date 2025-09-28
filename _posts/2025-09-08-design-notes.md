---
layout: post
title: "Design notes"
date: 2025-09-08
permalink: /design-notes
---

I’m a fan of the notion that one can[ unsee](http://gwern.net/unseeing) through notions like “expertise” and get things done no matter what the “[base rates”](https://en.wikipedia.org/wiki/Base_rate) and such similar notions *technically* say. One does not need to be or hire an expert in web design to make a good-looking website. One probably doesn’t even have to read a *textbook *on web design to make a good-looking website. In the year of our lord 2025, one can simply write out in excessive detail what one would like to see, and one’s[ talking, thinking machines](http://en.wikipedia.org/wiki/large_language_models) will hold up a mirror one can then edit at will.

Even before the year of our lord 2025, one could admire well-designed websites such as[ gwern.net](http://gwern.net/design) and steal from their looks whatever one wanted. It’s not a particularly difficult art, because[ nothing is inherently difficult](https://guzey.com/education/is-anything-inherently-difficult/)! Have taste; materialize that taste; rinse and repeat until your very own dot net has risen from the ground.

This page documents the “rising from the ground” that went behind croissanthology dot com. It’s not the design page per se, which will be[ here](http://croissanthology.com/design), at the time of this writing; that page will be for presenting the philosophy of the site, the exact[ CoT](https://en.wikipedia.org/wiki/Prompt_engineering#Chain-of-thought) behind every decision, the bits and pieces laid in full detail so as to be easier to copy. This article, meanwhile, will be messy: a wonderful[ bazaar](http://v), as many website pages ought to be.


## **404 Page**


Admire it[ here](http://croissanthology.com/404). I’m reading *Dracula* at the time I make this, in no small part because I’m attempting to allocate my downtime to consuming ~most fiction Gwern has written about, i.e. locally[ Suzanne Delage by Gene Wolf](http://gwern.net/suzanne-delage). The girl ChatGPT gave me from the prompt looked cute, so there she stands, guardian of my 404 page for all eternity. The way I coded things up[ˆ1], the 404 page will randomly alternate between several 404 page designs, just like on Gwern.net. I like this idea: it makes the website much richer, adds some rabbit holes to fall in, and will make for a pleasant afternoon designing another dozen of these before we’re ready to go.

But for now, this will suffice; I have other things to do, like designing footnotes.


![Croissanthology's 404 page, a young female vampire with white hair and lavender robes / headband holding an anthology of papers, some of which are fluttering in the wind. Small bat familiar on her shoulder.](https://imgur.com/RCVpXtK)



## **Footnotes**


Why footnotes are so !E*#&@&!& hard to design and implement (for me), I do not know. It may have to do with the fact that every[ croissanthology.com](http://croissanthology.com) page is a Google document, initially; and footnotes do not work intuitively-to-markdown on Google Docs. So I’ve given up on working with normal gdocs footnotes, and now I just write my footnotes directly in markdown and Jekyll parses that fine.

Now onto the actual design!


## Meta-data

There's more relevant information to a visitor who opens a post than the title and date. Specifically, completeness tags and importance tags seem like a useful addition. Visitors could at-a-glance see my rough estimate from 0-10 for how “important” a post ends up being, as measured by expected impact to one of humanity or the visitor. Posts on the lower end (such as the post you're reading!) are fun to write and I sometimes need to add to them when I'm feeling tired or not up to the task to do anything of note, but have to keep up my writing streak anyway (this is the situation I find myself in at the moment).


## List of future additions

- Little croissant icon for intralinks
- Footnotes! Still! Don’t! Look! Good!
- Table of contents not perfect yet
- Thy headings should not copy automatically, do the Gwern spinning link thing

[^1]:** **Or rather, had OpenAI Codex Web code things up while I was taking a stroll, shower, or otherwise not paying attention and occasionally adjusting details on my phone screen. One can lead an incredibly satisfying cadence of existence, even at our relatively primitive technological level.
