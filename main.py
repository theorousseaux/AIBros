from agent import AIBRO
import json
from models import State


def get_user_information(nickname: str):
    with open("personal_info/users.json", "r") as f:
        all_info = json.load(f)
    for user in all_info["users"]:
        if user["nickname"].lower() == nickname.lower():
            return user
    return {}


if __name__ == "__main__":

    user = "dozo"
    aibro = AIBRO()
    wf = aibro.define_graph()
    history = []
    while True:
        user_input = input("You: ")
        initial_state = State(
            user_info=get_user_information(user),
            question=user_input,
            chat_history=history,
            diet_plan=None,
            cookbook=None,
            response="",
        )
        if user_input.lower() == "exit":
            print(
                "AI-Bro: Alright, bro! It was great chatting with you. Stay strong and keep pushing!"
            )
            break

        for output in wf.stream(initial_state, debug=True):
            if "response" in output:
                print(output)

        # history.append(output["response"])
