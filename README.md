# Librarian RAG Agent

I wanted to teach myself PocketFlow, and I've been intrigued by RAG.

## PocketFlow
PocketFlow is a simple graph based framework for organizing agents, or really just objects that generate text. I like the workflow so far, particularly how it encourages sensible scoping and error handling without a lot of work. Plus, I'm closer to how the computer manages actually talking to the LLM service, which is a real blessing for dealing with provider specific quirks.

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

## Running this garbage
Put text based documents you'd like to search in `data_files`. I plopped in a few project gutenberg books because public domain and full of ambiguous details.

Start the program with `GOOGLE_API_KEY="YOUR_KEY_HERE" uv run main.py`. For now, all the bits are implemented with Gemini because it's cheap and has a huge context window. You're welcome to refactor call llm. Don't hardcode your keys, kids.
