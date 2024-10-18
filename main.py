from src.nutritionist.agent import NutritionPipeline
import json
from src.models import State
from src.all_tools import get_user_information

if __name__ == "__main__":

    user = "dozo"
    nutri_bro = NutritionPipeline()
    nutri_pipe = nutri_bro.pipeline()
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

        for output in nutri_pipe.stream(initial_state, debug=True):
            if "response" in output:
                print(output)

        # history.append(output["response"])
