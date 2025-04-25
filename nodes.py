from pocketflow import Node, BatchNode
from utils.call_llm import call_llm
import json

import os

from pathlib import Path

data_path = "data_files"

def get_documents(query):
    out = []
    for root, dirs, files in os.walk(data_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            # Process the file
            print(f"Processing file: {file_path}")
            with open(file_path, "r") as file:
                out += [(file_path, file.read())]
    return out

def list_documents():
    out = []
    for root, dirs, files in os.walk(data_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            # Process the file
            out += file_path
    return out

class GetQuestionNode(Node):
    def exec(self, _):
        # Get question directly from user input
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question
        shared["question"] = exec_res
        return "default"  # Go to the next node

class LibrarianNode(Node):
    def prep(self, shared):
        context = shared.get("context", [])
        question = shared["question"]
        filenames = list_documents()
        return question, filenames, context

    def exec(self, inputs):
        question, filenames, context = inputs
        print("Librarian node doing stuff...")
        print(context)
        prompt = f"""
Given question: {question}
List of files in datastore: {filenames}
Previous datastore analysis results: {context}
Should I: 1) Request an analysis of the datastore with a specific query to get more information 2) Answer with current knowledge?

Stick to specific queries that serve to fill gaps in the previous results, you can request further information on future iterations. Focus on atomic questions that can be used together for an answer

For example: ```Question: Compare the mental health of Dr. Frankenstein and Bartleby
query: What do Dr. Frankensteins words and actions say about his mental health?
[NEXT ITERATION]
query: What do Bartleby's words and actions say about his mental health?
```

Output your response as a JSON object within a ```json code block. The JSON object should have two keys: "action" and "reason". If the action is "query", include a third key "query" with the specific concept to analyze.

```json
{{
  "action": "query/answer",
  "reason": "why this action",
  "answer": "full answer to given question, if present"
  "query": "specific concept to analyze in datastore, phrased as a question, if present"
}}
```
"""
        resp = call_llm(prompt)
        json_str = resp.split("```json")[1].split("```")[0].strip()
        result = json.loads(json_str)
        
        assert isinstance(result, dict)
        assert "action" in result
        assert "reason" in result
        assert result["action"] in ["query", "answer"]
        if result["action"] == "query":
            assert "query" in result
        
        return result

    def post(self, shared, prep_res, exec_res):
        if exec_res["action"] == "query":
            print(f"query: {exec_res['query']}")
            shared["query"] = exec_res["query"]
        if exec_res["action"] == "answer":
            print(f"answer: {exec_res['answer']}")
            shared["answer"] = exec_res["answer"]
        print(exec_res["reason"])
        return exec_res["action"]

class RetrievalNode(Node):
    def prep(self, shared):
        # Get query
        return shared["query"]

    def exec(self, query):
        # TODO actual file selection
        # each document is filename: contents
        return get_documents(query)

    def post(self, shared, prep_res, documents):
        shared["docs"] = documents

class RelevanceNode(BatchNode):
    def prep(self, shared):
        return list(map(lambda x: (shared["query"], x), shared["docs"]))

    def exec(self, inputs): 
        query, doc = inputs
        filename, contents = doc
        prompt = f"""
Given document name: {filename}
Given document contents: {contents}
With query: {query}
Is this document at all relevant to the query? If even one piece of information could plausibly help answer the query, it is relevant.

Output your response as a JSON object within a ```json code block. The JSON object should have a single key: "relevant".

```json
{{
  "relevant": true/false
}}
```
"""
        print("Using LLM to judge relevance")
        resp = call_llm(prompt)
        json_str = resp.split("```json")[1].split("```")[0].strip()
        result = json.loads(json_str)


        assert isinstance(result, dict)
        assert 'relevant' in result
        # Handle both boolean true/false and string "true"/"false"
        if result['relevant'] is True or str(result['relevant']).lower() == "true":
            print(f"{filename} is relevant")
            return (query, doc)
        else:
            return None

    def post(self, shared, prep_res, exec_res_list):
        shared['relevant_docs'] = list(filter(lambda x: x != None, exec_res_list))

class EvidenceNode(BatchNode):
    def prep(self, shared):
        return shared['relevant_docs']

    def exec(self, inputs): 
        query, doc = inputs
        filename, contents = doc
        prompt = f"""
Given document name: {filename}
Given document contents: {contents}
With query: {query}
Transcribe whatever parts of the contents could be useful to answer the question, and put it in the following structured JSON.

Paraphrase or excise content using parenthesis around your edits where necessary for brevity/clarity. IE: "Today [we] are going to shower, eat breakfast, [...] and then go to bed." Prefer to create separate entries over glossing multiple details/sections together.

Do not be afraid to copy text that might be only part of an answer, you will later be mixing citations from many sources to form an analysis.

Explain the evidence in the citation in the "reason" field.

Example entry for query "Why is the sky blue?":
{{
  "content": "The sky is blue because of how the air scatters blue light.",
  "reason": "This explains why the sky is blue scientifically"
}}

If you can't make any entries, an empty entries list in the JSON is fine.

Output your response as a JSON object within a ```json code block. The JSON object should have a single key "entries" which is a list of objects, each with "content" and "reason" keys.

```json
{{
  "entries": [
    {{
      "content": "String",
      "reason": "String"
    }},
    {{
      "content": "String",
      "reason": "String"
    }}
  ]
}}
```"""
        print("Using LLM to generate citation entries")
        resp = call_llm(prompt)
        json_str = resp.split("```json")[1].split("```")[0].strip()
        result = json.loads(json_str)


        assert isinstance(result, dict)
        assert 'entries' in result
        assert isinstance(result['entries'], list)
        for entry in result['entries']:
            assert isinstance(entry, dict)
            assert 'content' in entry
            assert 'reason' in entry
        result['filename'] = filename
        return result

    def post(self, shared, prep_res, exec_res_list):
        shared['evidence'] = exec_res_list

class AnalysisNode(Node):
    def prep(self, shared):
        return (shared['query'], shared['evidence'])

    def exec(self, inputs):
        query, evidences = inputs
        prompt = f"""
Given document excerpts: {evidences}
With query: {query}

Write a concise analysis answering the query, or explaining why an answer isn't clear or available from the excerpts you have. When you use a citation, put the filename in parenthesis at the end of the sentence.
"""
        print("Using LLM to generate analysis...")
        resp = call_llm(prompt)
        return resp

    def post(self, shared, prep_res, exec_res):
        shared['analysis'] = exec_res
        shared['context'].append(exec_res)
        print(exec_res)

# Wire them in sequence
"""
chunk_node = ChunkDocs()
embed_node = EmbedDocs()
store_node = StoreIndex()

chunk_node >> embed_node >> store_node

OfflineFlow = Flow(start=chunk_node)
"""
