from agent import AgentState
from langgraph.graph import END, StateGraph, START
from langchain_core.messages import HumanMessage
from agent import AIBRO

if __name__ == "__main__":

    aibro = AIBRO()
    members = ["nutritionist", "bro"]  # , "personal_info_writer"]
    graph = aibro.create_graph(members=members)
    state = {"messages": []}

    print("Welcome to AI-Bro! Type 'exit' to end the conversation.")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print(
                "AI-Bro: Alright, bro! It was great chatting with you. Stay strong and keep pushing!"
            )
            break

        state["messages"].append(HumanMessage(content=user_input))

        for s in graph.stream(state):
            # for key in s.keys():
            #     if key == "bro":
            #         print(f"AI-Bro: {s[key]['messages'][-1].content} ")
            state = s
            print(s)

        state["messages"] = []
