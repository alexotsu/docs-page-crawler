# Page Crawler

## Usage

`python3 crawl.py <url> [-o <output-file>.txt] [-d <requests delay in seconds>]`

## Intro

Having [Google Notebook LM](https://notebooklm.google.com/) summarize docs pages is great, but since it cannot crawl multiple pages, a current limitation is needing to add the links one-by-one to the source.

This tool crawls the page for links of the same domain and dumps all the information into a single text doc, which can then be pasted into Notebook LM's context.

## Problem

Only one link can be uploaded at a time:

![only one link can be uploaded at a time](https://github.com/user-attachments/assets/4bc1db33-c8e6-4da4-bfb5-37818eed552f)

So for docs pages with many links (looking at you, GitBook!), you have to copy/paste a ton of times. Notebook LM also currently has a limit of 50 sources, so docs with more than 50 pages cannot be fully loaded in. The result looks like a mess and takes forever:

![messy source list](https://github.com/user-attachments/assets/8d6742e8-813c-40d3-b324-59976f60e00c)

This tool makes loading sources in a lot easier, and only takes up one space in the sources slot. So if you need more context, there is plenty more room.

![cleaned up version](https://github.com/user-attachments/assets/070c1490-7c57-4237-a511-dd136c0890be)
