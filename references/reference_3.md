A simple paragraph. With some text. Lorem ipsum lorem ipsum bla bla bla. After that, we will test putting empty space. See if empty space can survive a back-and-forth.


There were two empty lines before this one.

Let’s put in some deep nesting
- Like so
    - And deeper
        - And even deeper
            - How deep does the rabbit hole go?
                - Deeper than this
                    - Now we are cycling bullet formats. It’s a good time to stop
                - And come back

I also want to test some more esoteric behaviours of lists.
- Like
    - Inside a sub-item
    Breaking out of the list
    Putting a few lines like this
    - Then coming back to the list

How about toggle lists? I suspect that this is just not supported in Markdown.
- [>] This is a toggle
    First item
- [>] Another toggle
    - [>] With nested toggle
        Some text here

### [>] This is a toggle header
    And some content

<aside>
💡 And now for a Callout ! Let’s make it multiline
More text here
</aside>

It is also interesting to see the behaviour with internal links. Like the one below :
<notion-page id="24a86526-0e43-81ff-9831-f18a057c56c5"></notion-page>

What happens when we put an inline mention of a person? <notion-user id="158865cc-668a-4326-ae17-e02980141fff">@Maximolog</notion-user>
And an inline mention of a page <notion-page id="24a86526-0e43-81ff-9831-f18a057c56c5"></notion-page>

Let’s try some maths:
$E = mc^2$

And see how inline emojis are handled 🙂
And inline dates <notion-date>August 10, 2025</notion-date>

Now for multiple columns:
<notion-columns>
<notion-column>
This is the text in the column on the left. Let’s try and make it long enough to span multiple lines.
</notion-column>
<notion-column>
And this is the text in the column on the right. Similarly, let’s try and make it a tiny bit long.

Let’s write a bit more.

And more.
</notion-column>
</notion-columns>