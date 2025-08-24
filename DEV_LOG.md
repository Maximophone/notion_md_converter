## 2025-08-10

Today I am implementing a workflow where I create a complicated page on Notion with a lot of features and then I save the JSON that is returned by the API. 

## 2025-08-24

Ok, let's write down here the idea that I have for this library. At its very core, I want it to have three stable functions:
1. One function that takes the JSON that is returned by Notion for a specific page and turns it into the JSON that Notion accepts to create a page. Removing the block IDs, etc. We should figure out names for all of these data objects so that it's clear what we are talking about going forward. Let's think this through a bit. The JSON that is returned by Notion when you query a page contains information that is specific to that instance of the page. The IDs, the timestamps, etc. It's stuff that goes beyond the textual and formatting data. Let's call it "notion page snapshot JSON".
The JSON that we get after the conversion only contains the textual and formatting data. It is a lossy conversion, and you cannot go back to the original. Let's call it "notion page JSON".
Then we will have a function that turns the NotionPage Json into a Markdown string. And a function that turns the Markdown string into a NotionPage JSON. These operations should be fully invertable within the domain covered by this library. Actually, it would be nice to have them fully invertible regardless of the domain. So for example when a block is encountered from the JSON that we don't know how to convert there should be a syntax such that we put something in the Markdown that saves the content of the block so that the conversion the other way around can still happen. 
The operations composed together should be idempotent : conversion_json_to_md(conversion_md_to_json(A)) = A
and 
conversion_md_to_json(conversion_json_to_md(A)) = A

These three functions are the very core of the library. 
There is also a dataset that will be the core of the library, and that we will build up on as time goes by. 
This will contain sets of files:
- a reference for the NotionPageSnapshot Json
- the associated reference of NotionPage Json
- the associated MarkdownPage

They can be in a folder, and the naming makes it clear what is what. 
Something like:
- ref_name_snapshot.json -> the initial snapshot
- ref_name.json -> the snapshot converted into a payload
- ref_name.md -> the markdown page

There should be a test suite that runs the conversions on all the references. As time goes by, we can add more references and test more edge cases.

I also want to have the option to extend the conversion set. What I mean by this is that we can do the conversion from and to Markdown in different ways, with different markdown syntaxes.
For example, in Obsidian, there is a specific syntax for callouts that looks like this: 
> [!warning]
> This is a callout
By default, callouts in Notion are converted into aside XML blocks. 
<aside>
:emoji: This is a notion callout
</aside>
Which is fine for a first version, but in the future, I want to have the option to specify other ways to convert to data. 

We will not implement this right now, but we should keep this in mind when structuring the library. 

Beyond these core functionalities, I want there to be a minimalistic API with methods that allow one to fetch a page and to create a page while abstracting away from the user the intricacies of Notion: the fact that you can only upload 100 blocks at a time and you have to make multiple requests. 

And there should be also a script folder that contains a few useful scripts. One script that retrieves a page from Notion from a URL and saves it either as a JSON page snapshot, a JSON page or a Markdown page. 

And there should be another script that takes in a Markdown file and uploads it to Notion under a parent page. 

OK, let's talk about the changes that need to happen from the current state. First, at the moment, we only have the JSON page to Markdown conversion and Markdown to JSON page conversion, but the JSON snapshot to JSON page conversion is hidden under the "Convert and Create Page" example. The functionality to do this conversion needs to become part of the core. 
Also, at the moment, the tests only check the conversion between the JSON page and Markdown, but not the JSON snapshot to the JSON page. I have added references to the snapshots. The test should automatically discover all the references in the references folder. 

The minimalistic API should be created. 

The scripts folder should be created with the scripts that I asked for. Examples folder should be cleaned. 

The core features should be refactored with potential extensibility in mind. 

Once this is all done, a new README file should be produced. 

