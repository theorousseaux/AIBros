import pandas as pd

exercise_to_muscle_map = {
    "Squat": ["Quadriceps", "Glutes"],
    "Front Squat": ["Quadriceps", "Core"],
    "Bench Press": ["Chest", "Triceps", "Shoulders"],
    "Incline Bench Press": ["Upper Chest", "Triceps", "Shoulders"],
    "Decline Bench Press": ["Lower Chest", "Triceps"],
    "Deadlift": ["Back", "Hamstrings", "Glutes"],
    "Romanian Deadlift": ["Hamstrings", "Glutes", "Lower Back"],
    "Overhead Press": ["Shoulders", "Triceps"],
    "Barbell Row": ["Back", "Biceps"],
    "Pull-Up": ["Back", "Biceps"],
    "Push-Up": ["Chest", "Triceps", "Shoulders"],
    "Dumbbell Curl": ["Biceps"],
    "Tricep Extension": ["Triceps"],
    "Leg Press": ["Quadriceps", "Glutes"],
    "Sitted Leg Curl": ["Hamstrings"],
    "Standing Leg Curl": ["Hamstrings"],
    "Leg Curl": ["Hamstrings"],
    "Leg Extension": ["Quadriceps"],
    "Lateral Raise": ["Shoulders"],
    "Upright Row": ["Shoulders", "Traps"],
    "Chest Fly": ["Chest"],
    "Lat Pulldown": ["Back", "Biceps"],
    "Cable Row": ["Back", "Biceps"],
    "Dips": ["Chest", "Triceps", "Shoulders"],
    "Shoulder Press": ["Shoulders", "Triceps"],
    "Calf Raise": ["Calves"],
    "Hip Thrust": ["Glutes", "Hamstrings"],
    "Hammer Curl": ["Biceps"],
    "Bulgarian Split Squat": ["Quadriceps", "Glutes"],
    "Lunges": ["Quadriceps", "Glutes"],
    "Face Pull": ["Rear Deltoids", "Upper Back"],
    "Pec Deck": ["Chest"],
    "Sissy Squat": ["Quadriceps"],
    "Pistol Squat": ["Quadriceps", "Glutes"],
    "Muscle-up": ["Back", "Chest", "Arms"],
    "Seated Cable Row": ["Back", "Biceps"],
    "Bent-Over Lateral Raise": ["Rear Deltoids"],
    "Good Morning": ["Hamstrings", "Lower Back"],
    "Glute Bridge": ["Glutes", "Hamstrings"],
    "Skull Crusher": ["Triceps"],
    "Preacher Curl": ["Biceps"],
    "Concentration Curl": ["Biceps"],
    "Side Plank": ["Core"],
    "Russian Twist": ["Core"],
    "Leg Raise": ["Core"],
    "Hanging Knee Raise": ["Core"],
    "Abductors Machine": ["Abductors"],
    "Adductors Machine": ["Adductors"],
}


# Function 1: Exercise Tracker
def exercise_tracker(df, exercise_name):
    # Filter data for the specific exercise
    exercise_df = df[df["Exercise name"] == exercise_name]

    # Group by date to find the best set performance for each day (max weight * reps)
    best_sets = (
        exercise_df.assign(
            Performance=lambda x: x["Charge (kg)"] * x["Number of repetitions"]
        )
        .groupby("Date", as_index=False)["Performance"]
        .max()
    )

    return best_sets


def modified_exercise_tracker(df, exercise_name, equipment):
    # Filter data for the specific exercise
    cond = (df["Exercise name"] == exercise_name) & (df["Equipment"] == equipment)
    exercise_df = df[cond]

    # Group by date to find the best set based on the maximum weight lifted for each day
    # This keeps the "Charge (kg)" and corresponding "Number of repetitions" as separate columns
    best_sets = (
        exercise_df.loc[exercise_df.groupby("Date")["Charge (kg)"].idxmax()]
        .loc[:, ["Date", "Charge (kg)", "Number of repetitions"]]
        .rename(
            columns={
                "Charge (kg)": "Best Weight",
                "Number of repetitions": "Number of Reps",
            }
        )
        .drop_duplicates(
            subset="Date"
        )  # Ensure unique entries per date for the best set
        .reset_index(drop=True)
    )

    return best_sets


# Function 2: Calculate number of sets per muscle group per week
def sets_per_muscle_per_week(df, exercise_to_muscle_map):
    # Ensure the Date column is in datetime format for resampling
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    df["Week"] = df["Date"].dt.isocalendar().week  # Extract week number for grouping
    df["Year"] = df["Date"].dt.year  # Extract year to differentiate weeks across years

    # Initialize a dictionary to hold weekly muscle group sets count
    weekly_sets = {}

    for exercise, muscles in exercise_to_muscle_map.items():
        # Filter data for each exercise and count the sets per week
        exercise_sets = (
            df[df["Exercise name"] == exercise].groupby(["Year", "Week"]).size()
        )
        # Accumulate sets per muscle group per week
        for muscle in muscles:
            if muscle not in weekly_sets:
                weekly_sets[muscle] = exercise_sets
            else:
                weekly_sets[muscle] = weekly_sets[muscle].add(
                    exercise_sets, fill_value=0
                )

    # Convert the dictionary to a DataFrame for easier visualization
    weekly_sets_df = pd.DataFrame(weekly_sets).fillna(0).astype(int)
    return weekly_sets_df
