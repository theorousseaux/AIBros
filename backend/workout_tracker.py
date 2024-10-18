from .models import *
import pandas as pd


# def workout_to_dataframe(workout: Workout) -> pd.DataFrame:
#     rows = []
#     for set_obj in workout["sets"]:
#         row = {
#             "workout_date": datetime.now().strftime("%d/%m/%Y %H"),
#             "workout_name": workout["name"],
#             "set_id": set_obj["id"],
#             "exercise_name": set_obj["exercice"]["name"],
#             "charge_type": set_obj["exercice"]["charge_type"],
#             "muscles": ", ".join(set_obj["exercice"]["muscles"]),
#             "reps": set_obj["nb_reps"],
#             "charge": set_obj["charge"],
#             "rest": set_obj["rest"],
#         }
#         rows.append(row)

#     return pd.DataFrame(rows)

from collections import defaultdict


def workout_to_dataframe(workout: dict) -> pd.DataFrame:
    rows = []
    exercise_set_counter = defaultdict(int)

    for set_obj in workout["sets"]:
        exercise_name = set_obj["exercice"]["name"]
        exercise_set_counter[exercise_name] += 1

        row = {
            "workout_date": datetime.now().strftime("%d/%m/%Y %H h"),
            "workout_name": workout["name"],
            "set_id": exercise_set_counter[exercise_name],
            "exercise_name": exercise_name,
            "charge_type": set_obj["exercice"]["charge_type"],
            "muscles": ", ".join(set_obj["exercice"]["muscles"]),
            "reps": set_obj["nb_reps"],
            "charge": set_obj["charge"],
            "rest": set_obj["rest"],
        }
        rows.append(row)

    return pd.DataFrame(rows)


def add_workout_to_dataframe(workout: Workout, df: pd.DataFrame) -> pd.DataFrame:
    new_data = workout_to_dataframe(workout)
    return pd.concat([df, new_data], ignore_index=True)
