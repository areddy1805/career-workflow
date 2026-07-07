from src.llm.client import OMLXClient

client = OMLXClient()

print("HEALTH CHECK")
print(client.health_check())

print("\nMODEL TEST")

response = client.chat(
    messages=[
        {
            "role": "system",
            "content": (
                "Return exactly one category and nothing else: "
                "experience, compensation, location, availability, "
                "capability, or other."
            ),
        },
        {
            "role": "user",
            "content": "Have you built FastAPI-based model serving APIs?",
        },
    ],
    temperature=0.0,
    max_tokens=100,
)

print(response)
