# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.


### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool takes the agent's parses information of the user query as parameters and find an item or more from the 'listing.json', that fits those parameters.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): the discription of the item the user is intrested of purchasing (Noam double check)
- `size` (str): the size of the item the user is intrested of purchasing
- `max_price` (float): The maximum price the user is willing to pay for that item. 

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
If sucesseful, this tool wil return a list ('results') of a possible items (Noam add type - prob item ID) that fall into the cratiria above.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->

If the tool fails (meaning it didn't find an item that fits the paramaters above), it should stop the loop, and notify the user's that it was unable to find an item that fits their paramaters.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

This tool takes the first item from the selected items (the result for the search_listings tool), and match it with the current waredrobe the user has 'wardrobe_schema.json'

Noam - check if the information from the qurey can also be pharse into the waredrobe

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): Selected thrifting items that fits the user's paramaters.
- `wardrobe` (dict): Clothes the user already own.

Noam write how each item loocks like. 

**What it returns:**
<!-- Describe the return value -->

It returns pairs of item that can be styled togther

Noam be more presise on return type 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->

If the wardrobe is empty/no outfit can be suggested, the user will be prompt with a massage that no outfit suggestion can be made. The loop will be stoped

---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->

This tool takes the outfit suggestions from suggest outfit tool, and format the clothing combination into a social presentation.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (...): ...  Noam tuple? a pair of 2 items (dict: based on the json formating), teh thrifted and from the waredrobe. 

**What it returns:**
<!-- Describe the return value -->
This returns a fit card - a social media post description ready of the outfit of the 2 items. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->

If the outfit data is incomplete, the tool should prompt the user with no fit post avaiable. 

---
### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->
---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
---

search_listings:

Starts runing after reciving the phrased paramaters from the suer query. Once it's done, it produce 'results' (Noam add type).
If result is empty, set an error message in the session and return early. Else return the result.

at this stage, set selected_item = results[0] and proceed to suggest_outfit.

suggest_outfit:

After running suggest_outfit with the the selected item, and wardrobe. If wardobe is empty, set an error message in the session and return early. Else, return the outfit_suggestion described above (do noam)

create_fit_card:

After running creat_fit_card with outfit_suggestion from the suggest_outfit. If the outfit_suggestion is null (or empty), set an error message stating that a outfit segggestion can not be made therefore not a fit_card. else, return a fit card as describe above. 


## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->



---
## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Initially, the user requests an item description. FitFindr finds a piece that fits this description and triggers a recommendation engine to suggest an outfit with that piece. After a combination is chosen, it generates a shareable social media fit card. If it can't find an item in `search_listings()`, it handles the error by terminating the loop early (preventing subsequent tool calls later) and providing an informative message.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the user's request and identifies constraints for the item the user wants (`query="vintage graphic tee"`, `max_price=30`). It calls the first tool: `search_listings(query="vintage graphic tee", max_price=30)`. 

Note: If this tool returns an empty list or fails, the loop terminates here (early), sets an error message in the session state, and prevents subsequent tool calls from running.

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
Assuming Step 1 successfully finds an item, it returns a listing dictionary (e.g., Noam maybe it should be ID instead `{"title": "90s Vintage Harley Davidson Tee", "price": 25, "size": "L"}`). The agent saves this to the session state under `selected_item`. It then automatically triggers the recommendation engine by calling `suggest_outfit(item={"title": "90s Vintage Harley Davidson Tee", "price": 25, "size": "L"}, wardrobe_style="baggy jeans and chunky sneakers")` (wardrobe style constraints are from the intiall user request)

**Step 3:**
<!-- Continue until the full interaction is complete -->
The `suggest_outfit` tool returns a structured outfit combination string or dictionary incorporating the selected tee with the user's wardrobe style. The agent saves this to the session state under `outfit_suggestion`. Finally, it triggers the last tool by calling `create_fit_card(outfit_suggestion="...")` to format the clothing combination into a social  presentation.

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees the final formatted results in the UI panels, containing:
1. The matching secondhand item details found within their budget.
2. The recommended styling advice incorporating their existing wardrobe items.
3. A formatted, shareable social media "fit card" text summary ready to post.