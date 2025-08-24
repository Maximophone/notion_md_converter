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

*Same day, but after the AI log*
Okay so, I had an AI try to do the refactoring but there are still a lot of problems remaining with the core conversion. And it turns out that the problems were already there. They were just not being caught by the test because the previous test was only working on reference 1 and it was also not actually checking that the generated Markdown was the same as the reference Markdown. 

My focus should be on fixing these core issues.
Some examples I noticed:
- The Notion API returns a weird character for apostrophes. I think the simplest way to deal with this right now is to keep the weird character in the Markdown. 
- The indentation in sub-list items is off. And actually, this point makes me suddenly realize that we cannot have a fully idempotent two-way conversion. I write a bit more on this below. 
- Just noticed another potential problem with numbered lists. In Notion, you have the option to pick the symbol you want to have to number your list, but this seems to be lost by the API. This information is not in the payload. I think we will ignore this problem for now. Although there is still a problem with numbered_list because our conversion does not get the numbers and letters right. It should use the default for Notion: number -> letter -> lowercase roman numeral -> number -> ...
- Another problem is with the tables when we convert from the payload to a Markdown table, the indentation is lost. As in, each cell has exactly one space between its borders and the text it contains. Whereas our reference Markdown file has proper spacing. 

> [!warning]
> Yeah, I just realized that the fully idempotent conversion is not possible. An example of why is the indentation of lists. Notion does not offer flexibility on that. There is just a standard, and that's it. So, there is a loss of information when we convert from Markdown to Notion. The indentation information is lost. So we should not have an idempotency test in our test suite. 

*Same day, but after the latest AI log*

All right, we managed to make all the test pass. The core conversion seems to be working. 
Now the question is, what is the next step? I think I want to add the handling of databases, as in pages within databases.
Basically, that means that we must be able to handle page properties, so the payload object must preserve these. And the way I want to do it is by converting them to a front matter in the Markdown. What is a little bit tricky is that they need to be typed, as in the type must remain explicit. What I think we should do is have a specific syntax for the keys in the Markdown that indicates the type. It should also indicate that it's a Notion database property. 
Maybe something like this :
property in the database -> "Tag" of type "Select"
key in the frontmatter -> "ntn:select:Tag" (ntn for notion).

What I should do is start by adding a new reference for this in my list of references.
Ok, this is done. I have added reference_4_api.json.
The next step will be to modify the function that takes the API and converts it into a payload so that the properties are preserved and use that to generate the associated payload. In the meantime, we need to make sure that nothing else breaks by doing so specifically the API. And we need to update the other references so that the properties are preserved for them as well. 

Next we will have to define the associated reference markdown. 

*Same day, but after the latest AI log*

Okay, we have implemented the front matter to properties conversion; it's all working, but we are still missing a few properties. So the next step will be to handle relations roll-ups - basically all the remaining properties in Notion. 

Also, a little problem that needs to be solved is that for the files property, we actually need to save two things: the name and the URL. At the moment, we only save the URL. So, we need to figure out how to handle this. 