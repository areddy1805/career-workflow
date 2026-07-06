from config.candidate_profile import CANDIDATE_PROFILE
from src.llm.client import OMLXClient
from src.llm.question_resolver import LLMQuestionResolver
from src.resolution.hybrid_resolver import HybridQuestionResolver


client = OMLXClient(
    model="qwen3.5-4b",
)

llm_resolver = LLMQuestionResolver(
    client=client,
)

resolver = HybridQuestionResolver(
    llm_resolver=llm_resolver,
)


questions = [
    {
        "questionId": "1",
        "questionName": "How many years of experience do you have in RAG?",
        "questionType": "Text Box",
        "answerOption": {},
    },
    {
        "questionId": "2",
        "questionName": (
            "Have you built FastAPI-based model serving APIs "
            "and microservices?"
        ),
        "questionType": "Text Box",
        "answerOption": {},
    },
    {
        "questionId": "3",
        "questionName": (
            "Have you designed or implemented rule engines, "
            "business rules, or heuristic decision-making frameworks?"
        ),
        "questionType": "Text Box",
        "answerOption": {},
    },
    {
        "questionId": "4",
        "questionName": (
            "How long has your GenAI use case been deployed "
            "in production?"
        ),
        "questionType": "Text Box",
        "answerOption": {},
    },
    {
        "questionId": "5",
        "questionName": "What is your notice period?",
        "questionType": "List Menu",
        "answerOption": {
            "1": "30 Days",
            "2": "60 Days",
            "3": "90 Days",
        },
    },
]


for question in questions:
    print("=" * 100)
    print("QUESTION:")
    print(question["questionName"])

    result = resolver.resolve(
        question=question,
        profile=CANDIDATE_PROFILE,
    )

    print("\nSTATUS:")
    print(result.status)

    print("\nSOURCE:")
    print(result.source)

    print("\nSEMANTIC ANSWER:")
    print(result.semantic_answer)

    print("\nSERIALIZED ANSWER:")
    print(result.serialized_answer)

    print("\nCONFIDENCE:")
    print(result.confidence)

    print("\nREASONING:")
    print(result.reasoning)

    print()
