import { useState, useEffect } from 'react'
import NavBar from '../NavBar/NavBar';
import './Nutrition.css';

// The four daily nutrition targets
type nutritionTargets = {
    calories: number; // kcal
    protein: number;  // grams
    carbs: number;    // grams
    fat: number;      // grams
}

export default function Nutrition(){
    //These values will come from the backend later (based on the user's profile and goal)
    const [targets, setTargets] = useState<nutritionTargets>({ calories: 0, protein: 0, carbs: 0, fat: 0 });

    // Fills the target cards (hardcoded until the backend is connected)
    const getNutritionTargets = () => {
        setTargets({ calories: 2650, protein: 165, carbs: 320, fat: 75 });
    }

    // Load the targets once when the page first renders
    useEffect(() => {
        getNutritionTargets();
    }, []);

    // The four cards shown at the top (label + formatted value)
    const targetCards = [
        { label: 'Calories', value: `${targets.calories.toLocaleString()} kcal` },
        { label: 'Protein', value: `${targets.protein} g` },
        { label: 'Carbs', value: `${targets.carbs} g` },
        { label: 'Fat', value: `${targets.fat} g` },
    ];

    return (
        <div className='nutrition'>
            <NavBar />
            <main className='nutrition-main'>
                <h1 className='page-title'>Nutrition</h1>
                <p className='page-subtitle'>Simple daily targets that support your current fitness goal.</p>

                {/* Four target cards */}
                <div className='stats-row'>
                    {targetCards.map((card) => (
                        <div className='stat-card' key={card.label}>
                            <span className='stat-label'>{card.label}</span>
                            <span className='stat-value'>{card.value}</span>
                        </div>
                    ))}
                </div>

                {/* Large placeholder card */}
                <div className='todays-targets card'>
                    <h2>Today's targets</h2>
                    <p>This is placeholder UI for Week 1. Later, these values can come from the backend based on the user's profile and goal.</p>
                </div>
            </main>
        </div>
    );
}