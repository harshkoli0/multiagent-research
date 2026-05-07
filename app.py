from graph.workflow import app
from rich import print



query = input("Enter your query: ")


response = app.invoke({
    "query": query
})


print("\n")
print("FINAL RESPONSE")
print("=" * 50)
print(response["final"])