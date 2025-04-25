from pocketflow import Flow
from nodes import GetQuestionNode, LibrarianNode, RetrievalNode, RelevanceNode, EvidenceNode, AnalysisNode, AnswerNode

def create_qa_flow():
    """Create and return a question-answering flow."""
    # Create nodes
    get_question_node = GetQuestionNode()
    librarian_node = LibrarianNode(max_retries = 3)
    retrieval_node = RetrievalNode()
    relevance_node = RelevanceNode(max_retries = 3)
    evidence_node = EvidenceNode(max_retries = 3)
    analysis_node = AnalysisNode(max_retries = 3)
    answer_node = AnswerNode()
    
    # Connect nodes in sequence
    get_question_node >> librarian_node 

    librarian_node - "query" >> retrieval_node >> relevance_node >> evidence_node >> analysis_node >> librarian_node

    librarian_node - "answer" >> answer_node
    
    # Create flow starting with input node
    return Flow(start=get_question_node)
