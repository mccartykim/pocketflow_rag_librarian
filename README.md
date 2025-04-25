# Librarian RAG Agent

I wanted to teach myself PocketFlow, and I've been intrigued by RAG.

## PocketFlow
PocketFlow is a simple graph based framework for organizing agents, or really just objects that generate text. I like the workflow so far, particularly how it encourages sensible scoping and error handling without a lot of work. Plus, I'm closer to how the computer manages actually talking to the LLM service, which is a real blessing for dealing with provider specific quirks.

The heart of PocketFlow is the Node abstraction. Each Node is just three methods, prep, exec, and post. To manage mutable state, PocketFlow passes around a `shared` dictionary between nodes, so nodes can add/modify fields and use it as a global scope. However, it's not exposed durin the stage where you actually run the LLM, since that stage is prone to errors and retries.

*Prep* is for getting together whatever inputs we'll need before doing the compute heavy exec step. This method then returns a result that's then the input for `exec`. Use this step to unwrap data from the shared object or make API calls.

*Exec* just takes the class's self and the result from prep as its parameter. Shared is out of scope, and if you mess with it via global scope, please don't. This method is supposed to only change things if it succeeds. This method also returns a result, which then goes to *Post*.

*Post* is where we handle the outcome of exec if it was successful. So, we might take some of an LLM's output and return it in `exec`, and then pack it away in `shared` under post, and post returns a string that's meant to reflect its status. This is where agents can do branching behaviors.

Then, these nodes are joined with the `>>` method all dsl-ly to make a glorified object oriented state machine. I actually find the OOP abstractions useful for dealing with this LLM weirdness, because OOP is based on the idea objects encapsulate and hide their state but manage just fine by sharing messages with other objects with just the info they should care about. This is frustrating sometimes with imperative code, but LLMs are a black box by design. They are easiest to reason about when we think of them as a closure that spits out a variable length string based on unknown and complicated state.

These circuits of nodes are called *Flows*, and flows can also behave as nodes, so you could write an agent that really just uses a bunch of smaller agents without too much of a headache

The project is very proud to have implemented all of this in under 100 lines of python, which makes it easy to reason about as a human, and easy to fit inside an LLM's context. The project also makes sure to include plenty of hintfiles for different AI assistants, and sample code snippets for popular tools. I really like this approach since other than actually designing the agents, most of this stuff is glue code, the easiest kind of code for vibe coding.


## RAG - Retrieval Augmented Generation
Briefly, RAG is a way of giving LLMs more information than they've internalized from training. This is good, because this gets around small context windows. Who knows why these things do anything, but having good information in their context seems to make them halucinate less.

There's all kinds of RAG schemes, with the simplest probably just being dumping files into context, and more sophisticated ones using embeddings to find semantic matches.

The biggest problem with RAG is knowing what data to feed to the LLM, and some ML scientists think search is the fundamental problem of intelligence. That is, thinking is literally _finding the answer_. LLMs are clever enough to be spooky, but not terribly smart, so expecting them to write good queries over data they don't fully understand is a big ask.

I was most intrigued by [this paper](https://arxiv.org/abs/2407.19813), which breaks up the RAG process into a few agentic steps.

So, say I have a query and can get a stack of documents that fit in context that might fit that query. The first step is to determine _which of those documents are relevant_. The paper suggests using a vector embedding system to get the list of candidate documents, but in my case I just load all the files in the data_files directory. I'd like to change that, but for now the simplicity suits me. To get to the next step, we have an LLM look at the query and the contents of the file and just answer if the file is relevant or not.

If the file is relevant, we then go to the next node to find evidence relevant to the query. So, *an llm loads the file, and creates a structured output with a list of excerpts and why they might be useful for the query*. Note that this doesn't necessarily find concrete answers, it's just reducing the document to the most relevant bits in isolation.

Then, using those citations and partial thoughts about them in one big list, we formulate a final analysis, hopefully merging together a satisfying answer.

Currently, my implementation has a few weaknesses. Right now, it does a per file analysis instead of mixing citations from multiple sources, which I think can be my next refinement. I'd also like to use vector embeddings or maybe a keyword search to get the first set of documents. This might also allow us to use smaller models and still get good results. For now, Gemini's massive context window saves the day, and mocks me, because I could easily fit three or four gutenberg novels in there.

## Ideas I might implement
- Merge citations from evidence state from multiple documents for analysis stage
  - Note: This was a bit problematic in my early attempts, the model was a bit too giddy to reject documents as irrelevant, so I had the Librarian node handle asking for multiple smaller, more specific analysis that should just use one or two documents.
- Local models to deteremine relevance (Perhaps finetuning off of Gemini output?)
- Multimodal file input
  - Not that hard with gemini's sdk, we could easily make this a system to look up podcast and movie minutia, with enough money. The model is a vision/transcription model "for free."
- Local models to generate evidence
- Chunking documents to work with smaller models
- Build a knowledge graph from these results as a smaller, more human readable world model, that's also faster to query and more fluid than the whole analysis.
- Make Librarian an MCP server that takes an arbitrary data directory as a parameter
- Context caching

## Running this garbage
Put text based documents you'd like to search in `data_files`. I plopped in a few project gutenberg books because public domain and full of ambiguous details.

Start the program with `GOOGLE_API_KEY="YOUR_KEY_HERE" uv run main.py`. For now, all the bits are implemented with Gemini because it's cheap and has a huge context window. You're welcome to refactor call llm. Don't hardcode your keys, kids. If you need an API key from google, [this is the webpage for it](https://aistudio.google.com/apikey), you'll need to make a project. Smoke testing this repo like crazy only managed to spend me $1.15, and that's with no prompt caching and naively uploading all of _Frankenstein_ and friends on every Relevance query.

## Example output
I'm too lazy to tidy up my debug prints lol, deleting some extra lines here and there. Also, spoilers for some old books.

```
Enter your question: Which of these books has the happiest ending?
Librarian node doing stuff...

query: Describe the ending of 'yellow_wallpaper.txt'
rationale: To determine which book has the happiest ending, I need to know the ending of each book. I will start by querying the ending of 'yellow_wallpaper.txt'.
Processing file: data_files/yellow_wallpaper.txt
Processing file: data_files/bartleby.txt
Processing file: data_files/frankenstein.txt
Using LLM to judge relevance
data_files/yellow_wallpaper.txt is relevant

Using LLM to generate citation entries
Using LLM to generate analysis...
Analysis: Based on the excerpts, the ending of "yellow_wallpaper.txt" details the narrator's successful completion of removing the wallpaper, which she sees as freeing the "woman" trapped within the pattern. Having isolated herself by locking the door and throwing away the key, the narrator fully embraces her delusion, adopting the habit of creeping along the floor, identifying with the woman she believes she has released (data_files/yellow_wallpaper.txt). When her husband, John, finally gains entry, he finds the room in disarray and the narrator creeping around the floor (data_files/yellow_wallpaper.txt). She declares that she has "got out at last" and has removed the paper so she cannot be put "back," attributing her actions as an escape from John and Jane (data_files/yellow_wallpaper.txt). The ending culminates with John fainting in shock, lying across her path, leaving the narrator to continue creeping over him (data_files/yellow_wallpaper.txt).

Librarian node doing stuff...
query: What happens at the end of 'bartleby.txt'?
Rationale: To determine which book has the happiest ending, I need to know the endings of 'bartleby.txt' and 'frankenstein.txt'. I currently only have information about the ending of 'yellow_wallpaper.txt', which appears to be unhappy. Requesting analysis of one of the remaining book endings.
Processing file: data_files/yellow_wallpaper.txt
Processing file: data_files/bartleby.txt
Processing file: data_files/frankenstein.txt
Using LLM to judge relevance
Using LLM to judge relevance
data_files/bartleby.txt is relevant

Using LLM to generate citation entries
Using LLM to generate analysis...
Based on the excerpts, the end of the story involves Bartleby remaining at the narrator's old office building after the narrator moves, refusing to leave and eventually being found living in the common areas (bartleby.txt). The new occupant and landlord demand the narrator remove Bartleby (bartleby.txt). The narrator makes one final attempt to reason with Bartleby and offer him lodging, which Bartleby refuses (bartleby.txt). Ultimately, the landlord has Bartleby arrested as a vagrant and taken to the Tombs prison (bartleby.txt). Bartleby passively accepts this (bartleby.txt). The narrator visits Bartleby in prison, but Bartleby refuses to speak to him (bartleby.txt). The narrator later learns that Bartleby died in prison, having apparently refused to eat (bartleby.txt). The story concludes with the narrator recounting a rumor that Bartleby previously worked in the Dead Letter Office, suggesting this experience may have contributed to his state (bartleby.txt).

Librarian node doing stuff...
query: Describe the ending of the book frankenstein.txt
Rationale: To determine which book has the happiest ending, I need to know the ending of Frankenstein, as the endings of The Yellow Wallpaper and Bartleby have been analyzed and appear unhappy.
Processing file: data_files/yellow_wallpaper.txt
Processing file: data_files/bartleby.txt
Processing file: data_files/frankenstein.txt
Using LLM to judge relevance
Using LLM to judge relevance
Using LLM to judge relevance
data_files/frankenstein.txt is relevant
Using LLM to generate citation entries
Using LLM to generate analysis...
Based on the provided excerpts, the ending of *Frankenstein* details the final fates of both Victor Frankenstein and his Creature.

Victor Frankenstein's life ends in a long, arduous pursuit of the Creature across vast distances and into the Arctic ice after suffering the deaths of his loved ones, including his father (data_files/frankenstein.txt). Having survived a mental breakdown and imprisonment following these tragedies, Victor becomes consumed by revenge (data_files/frankenstein.txt). His chase leads him to near-fatal exhaustion, and he eventually dies on board Captain Walton's ship, still regretting his failure to destroy the Creature (data_files/frankenstein.txt).

After Victor's death, the Creature appears in the cabin, mourning over his creator's body and expressing remorse for his actions, acknowledging Victor as his final victim (data_files/frankenstein.txt). He explains to Walton the mix of anguish, remorse, and vengeance that drove him (data_files/frankenstein.txt). Finally, the Creature declares his intention to end his own life by traveling to the northernmost pole and burning himself on a funeral pyre, ensuring his complete destruction and preventing the possibility of another like him being created. He then departs Walton's ship on an ice raft, heading towards his self-imposed death (data_files/frankenstein.txt).

Librarian node doing stuff...
Final context: ['Based on the excerpts, the ending of "yellow_wallpaper.txt" details the narrator\'s successful completion of removing the wallpaper, which she sees as freeing the "woman" trapped within the pattern. Having isolated herself by locking the door and throwing away the key, the narrator fully embraces her delusion, adopting the habit of creeping along the floor, identifying with the woman she believes she has released (data_files/yellow_wallpaper.txt). When her husband, John, finally gains entry, he finds the room in disarray and the narrator creeping around the floor (data_files/yellow_wallpaper.txt). She declares that she has "got out at last" and has removed the paper so she cannot be put "back," attributing her actions as an escape from John and Jane (data_files/yellow_wallpaper.txt). The ending culminates with John fainting in shock, lying across her path, leaving the narrator to continue creeping over him (data_files/yellow_wallpaper.txt).', "Based on the excerpts, the end of the story involves Bartleby remaining at the narrator's old office building after the narrator moves, refusing to leave and eventually being found living in the common areas (bartleby.txt). The new occupant and landlord demand the narrator remove Bartleby (bartleby.txt). The narrator makes one final attempt to reason with Bartleby and offer him lodging, which Bartleby refuses (bartleby.txt). Ultimately, the landlord has Bartleby arrested as a vagrant and taken to the Tombs prison (bartleby.txt). Bartleby passively accepts this (bartleby.txt). The narrator visits Bartleby in prison, but Bartleby refuses to speak to him (bartleby.txt). The narrator later learns that Bartleby died in prison, having apparently refused to eat (bartleby.txt). The story concludes with the narrator recounting a rumor that Bartleby previously worked in the Dead Letter Office, suggesting this experience may have contributed to his state (bartleby.txt).", "Based on the provided excerpts, the ending of *Frankenstein* details the final fates of both Victor Frankenstein and his Creature.\n\nVictor Frankenstein's life ends in a long, arduous pursuit of the Creature across vast distances and into the Arctic ice after suffering the deaths of his loved ones, including his father (data_files/frankenstein.txt). Having survived a mental breakdown and imprisonment following these tragedies, Victor becomes consumed by revenge (data_files/frankenstein.txt). His chase leads him to near-fatal exhaustion, and he eventually dies on board Captain Walton's ship, still regretting his failure to destroy the Creature (data_files/frankenstein.txt).\n\nAfter Victor's death, the Creature appears in the cabin, mourning over his creator's body and expressing remorse for his actions, acknowledging Victor as his final victim (data_files/frankenstein.txt). He explains to Walton the mix of anguish, remorse, and vengeance that drove him (data_files/frankenstein.txt). Finally, the Creature declares his intention to end his own life by traveling to the northernmost pole and burning himself on a funeral pyre, ensuring his complete destruction and preventing the possibility of another like him being created. He then departs Walton's ship on an ice raft, heading towards his self-imposed death (data_files/frankenstein.txt)."]
answer: Based on the analyses provided, none of these books have a happy ending. 'The Yellow Wallpaper' ends with the narrator's complete mental breakdown, 'Bartleby' ends with the character's death in prison, and 'Frankenstein' ends with the deaths of both Victor Frankenstein and his Creature in tragic circumstances.
Rationale: Based on the provided analyses of the endings for 'The Yellow Wallpaper', 'Bartleby, the Scrivener', and 'Frankenstein', none of the books have what could be considered a happy ending. 'The Yellow Wallpaper' ends with the narrator's descent into complete delusion. 'Bartleby' ends with the title character's death in prison. 'Frankenstein' ends with the deaths of both the protagonist and the creature, marked by tragedy and despair.

Question: Which of these books has the happiest ending?
Answer: Based on the analyses provided, none of these books have a happy ending. 'The Yellow Wallpaper' ends with the narrator's complete mental breakdown, 'Bartleby' ends with the character's death in prison, and 'Frankenstein' ends with the deaths of both Victor Frankenstein and his Creature in tragic circumstances.```
