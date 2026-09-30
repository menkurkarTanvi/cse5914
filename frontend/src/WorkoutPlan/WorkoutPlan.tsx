import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom';
import './WorkoutPlan.css';
import NavBar from '../NavBar/NavBar';


// One exercise in a given day's workout
type workoutsForGivenDay = {
    workoutName: string;
    sets: number;
    reps: string; // string so we can show ranges like "8–10"
    weight: number;
    equipment: string;
}

// One entry in the "This week" list
type dayOfWeek = {
    key: string;     // used as the selectedDay value
    label: string;   // shown in the "This week" list
    title: string;   // shown as the card heading
    muscles: string; // shown under the card heading
}

// The 4 training days of the week (placeholder until the backend is connected)
const weekSchedule: dayOfWeek[] = [
    { key: 'monday', label: 'Mon — Push', title: 'Monday — Push', muscles: 'Chest, shoulders, triceps' },
    { key: 'tuesday', label: 'Tue — Pull', title: 'Tuesday — Pull', muscles: 'Back, biceps, rear delts' },
    { key: 'thursday', label: 'Thu — Legs', title: 'Thursday — Legs', muscles: 'Quads, hamstrings, glutes, calves' },
    { key: 'saturday', label: 'Sat — Upper', title: 'Saturday — Upper', muscles: 'Chest, back, shoulders, arms' },
];

// Placeholder exercises for each day (will come from the backend later)
const placeholderWorkouts: { [day: string]: workoutsForGivenDay[] } = {
    monday: [
        { workoutName: 'Barbell Bench Press', sets: 3, reps: '8–10', weight: 0, equipment: 'Barbell' },
        { workoutName: 'Incline Dumbbell Press', sets: 3, reps: '8–10', weight: 0, equipment: 'Dumbbell' },
        { workoutName: 'Shoulder Press', sets: 3, reps: '10', weight: 0, equipment: 'Dumbbell' },
        { workoutName: 'Lateral Raises', sets: 3, reps: '12–15', weight: 0, equipment: 'Dumbbell' },
    ],
    tuesday: [
        { workoutName: 'Pull-Ups', sets: 3, reps: '8–10', weight: 0, equipment: 'Bodyweight' },
        { workoutName: 'Barbell Row', sets: 3, reps: '8–10', weight: 0, equipment: 'Barbell' },
        { workoutName: 'Face Pulls', sets: 3, reps: '12–15', weight: 0, equipment: 'Cable' },
        { workoutName: 'Dumbbell Curls', sets: 3, reps: '10–12', weight: 0, equipment: 'Dumbbell' },
    ],
    thursday: [
        { workoutName: 'Back Squat', sets: 3, reps: '8–10', weight: 0, equipment: 'Barbell' },
        { workoutName: 'Romanian Deadlift', sets: 3, reps: '8–10', weight: 0, equipment: 'Barbell' },
        { workoutName: 'Leg Press', sets: 3, reps: '10–12', weight: 0, equipment: 'Machine' },
        { workoutName: 'Calf Raises', sets: 3, reps: '12–15', weight: 0, equipment: 'Machine' },
    ],
    saturday: [
        { workoutName: 'Incline Bench Press', sets: 3, reps: '8–10', weight: 0, equipment: 'Barbell' },
        { workoutName: 'Seated Cable Row', sets: 3, reps: '10', weight: 0, equipment: 'Cable' },
        { workoutName: 'Arnold Press', sets: 3, reps: '10–12', weight: 0, equipment: 'Dumbbell' },
        { workoutName: 'Triceps Pushdown', sets: 3, reps: '12–15', weight: 0, equipment: 'Cable' },
    ],
};

export default function WorkoutPlan(){
    const navigate = useNavigate();
    //These function will be implemented later
    const [workoutName, setWorkoutName] = useState('');
    const [workoutGoal, setWorkoutGoal] = useState('');
    const [selectedDay, setSelectedDay] = useState('monday');
    const [workoutPlan, setWorkoutPlan] = useState<workoutsForGivenDay[]>([]);
    // Tracks which days have been marked complete
    const [completedDays, setCompletedDays] = useState<string[]>([]);

    const getWorkoutName = () => {
        setWorkoutName("4-day hypertrophy plan");
    }

    const getGoal = () => {
        setWorkoutGoal("Goal: Build muscle • 60 min/session • Full gym");
    }

    const handleAICoachClick = () => {
        //Not implemented right now, but will navigate to the AI Coach page when clicked
        navigate('/ai-coach');
    }

    const getWorkoutPlanForDay = (day: string) => {
        //This function will be implemented later to get the workout plan for the selected day
        //For now it loads the placeholder exercises for that day
        setWorkoutPlan(placeholderWorkouts[day] || []);
    }

    // Placeholder: swapping exercises will be handled later (likely through the AI Coach)
    const handleSwapExercise = (exerciseName: string) => {
        console.log('Swap exercise:', exerciseName);
    }

    // Marks the selected day as complete (only once)
    const handleMarkComplete = () => {
        if (!completedDays.includes(selectedDay)) {
            setCompletedDays([...completedDays, selectedDay]);
        }
    }

    // Load the plan header once when the page first renders
    useEffect(() => {
        getWorkoutName();
        getGoal();
    }, []);

    // Reload the exercises whenever a different day is selected
    useEffect(() => {
        getWorkoutPlanForDay(selectedDay);
    }, [selectedDay]);

    // Info for the currently selected day (falls back to Monday)
    const currentDay = weekSchedule.find((d) => d.key === selectedDay) || weekSchedule[0];
    const isComplete = completedDays.includes(selectedDay);


    return (
        <div className='workout-plan-layout'>
            {/* Left sidebar with logo and navigation */}
            <NavBar />

            {/* Main page content */}
            <main className='workout-plan'>
                <h1 className='page-title'>Workout Plan</h1>
                <p className='page-subtitle'>Personalized from your profile and updated with your feedback.</p>

                {/* Plan name, goal and AI Coach button */}
                <div className='workout-plan-name card'>
                    <div>
                        <h2>{workoutName}</h2>
                        <p>{workoutGoal}</p>
                    </div>
                    <button className='ask-coach-button' onClick={handleAICoachClick}>Ask AI Coach</button>
                </div>

                <div className='workout-plan-grid'>
                    {/* "This week" list of training days (replaces the day dropdown) */}
                    <div className='select-day-of-week card'>
                        <h2>This week</h2>
                        {weekSchedule.map((day) => (
                            <button
                                key={day.key}
                                className={day.key === selectedDay ? 'day-button active' : 'day-button'}
                                onClick={() => setSelectedDay(day.key)}
                            >
                                {day.label}
                            </button>
                        ))}
                    </div>

                    {/* Exercises for the selected day */}
                    <div className='workout-plan-for-day card'>
                        <h2>{currentDay.title}</h2>
                        <p className='day-muscles'>{currentDay.muscles}</p>
                        <div className='exercise-list'>
                            {workoutPlan.map((exercise) => (
                                <div className='exercise-item' key={exercise.workoutName}>
                                    <div>
                                        <h3>{exercise.workoutName}</h3>
                                        <p>{exercise.sets} × {exercise.reps}</p>
                                    </div>
                                    <button className='swap-button' onClick={() => handleSwapExercise(exercise.workoutName)}>Swap exercise</button>
                                </div>
                            ))}
                        </div>
                        <div className='complete-row'>
                            <button className='complete-button' onClick={handleMarkComplete} disabled={isComplete}>
                                {isComplete ? 'Workout Completed' : 'Mark Workout Complete'}
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
