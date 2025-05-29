---
layout: post
title: "Do you even have a system prompt?"
date: 2025-05-29
permalink: /system-prompt
---

Everyone around me has a notable lack of system prompt. And when they do have a system prompt, it’s either the [eigenprompt](https://x.com/eigenrobot/status/1782957877856018514) or some half-assed 3-paragraph attempt at telling the AI to “include less bullshit”.


I see no systematic attempts at making a good one *anywhere*.1


No one says “I have a conversation with Claude, then edit the system prompt based on what annoyed me about its responses, then I rinse and repeat”. No one says “I figured out what words most affect Claude's behavior, then used those to shape my system prompt". I don't even see a “yeah I described what I liked and didn't like about Claude to Claude and then had it make a system prompt for itself”, which is the EASIEST bar to clear.


So if you're reading this and don't use a personal system prompt, STOP reading this and go DO IT. Spend 5 minutes on a google doc being as precise as you can about how you want the LLM to act.


It doesn’t matter if you think it cannot properly respect these instructions—this’ll make the LLM marginally better at accommodating you (and I think you’d be surprised how far it can go).


# Help how do I do this?


For clarity, a system prompt is a bit of text—also called “preset” or “context”—that's included in every single message you send the AI.


There’s no downside to using one except that it takes more tokens (which costs you more if you’re in the playground or API, or makes you reach usage limits faster if you’re on a subscription plan).


If you’re on the **free ChatGPT plan**, you’ll want to use “settings → customize ChatGPT”, which gives you this popup:




The text box is very short and you won’t get much in.


If you’re on the **free **[Claude](Claude.ai)** plan**, you’ll want to use “settings → personalization”, where you’ll see almost the exact same textbox, except that Anthropic allows you to put *practically an infinite amount of text in here.*




If you get a **ChatGPT or Claude subscription**, you’ll want to stick this into “special instructions” in a newly created “project”, where you can stick other kinds of context in too.


What else can you put in a project, you ask? Say, a pdf containing the broad outlines of your life plans, or past examples of your writing or coding style, or a list of terms and definitions you’ve coined yourself. Try sticking the entire [list of LessWrong vernacular](https://www.lesswrong.com/w/lesswrong-canon-on-rationality) into it!


In general, the more information you stick into the prompt, the better for you.

If you're using the playground versions ([console.anthropic.com](http://console.anthropic.com), [platform.openai.com](http://platform.openai.com), [aistudio.google.com](http://aistudio.google.com)), you have access to writing a system prompt.


A **gemini subscription** doesn’t give you access to a system prompt, but you should be using [aistudio.google.com](aistudio.google.com) anyway, which is free anyway.


If you use LLMs via API, you just stick your system prompt into the context.
