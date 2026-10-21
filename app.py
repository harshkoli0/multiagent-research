import sys

from graph.workflow import build_app
from rich import print


# Query can be passed as arguments (python app.py "my question") or typed interactively
query = " ".join(sys.argv[1:]) or input("Enter your query: ")


app = build_app()
response = app.invoke({
    "query": query
})


print("\n")
print("PLAN")
print("=" * 50)
print(response["plan"])

print("\n")
print(f"SOURCES ({len(response['sources'])})")
print("=" * 50)
for i, s in enumerate(response["sources"], 1):
    print(f"[{i}] {s['title']} - {s['url']}")

print("\n")
print("FINAL RESPONSE")
print("=" * 50)
print(response["final"])