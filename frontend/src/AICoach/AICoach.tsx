import { useState } from 'react'
import NavBar from '../NavBar/NavBar';
import './AICoach.css';

// One message in the chat (either from the user or the AI)
type ChatMessage = {
    sender: 'user' | 'ai';
    text: string;
    title?: string; // optional bold headline for AI replies
}

// Placeholder workout shown in the "Current workout" card (will come from the backend later)
const currentWorkout = {
    name: 'Monday — Push',
    exercises: ['Barbell Bench Press', 'Incline Dumbbell Press', 'Shoulder Press', 'Lateral Raises'],
};

// Quick action buttons in the left card
const quickActions = ['Swap an exercise', 'Shorten workout', 'Adjust difficulty'];

export default function AICoach(){
    // What the user is currently typing in the input box
    const [userInput, setUserInput] = useState('');
    // Every message in the chat, in order (replaces the separate userInput / AIOutput / combinedOutput lists)
    // Starts with the example conversation from the design
    const [combinedOutput, setCombinedOutput] = useState<ChatMessage[]>([
        { sender: 'user', text: "I don't have a barbell today. What can I do instead?" },
        { sender: 'ai', title: 'Try dumbbell bench press as the closest substitute.', text: 'Keep the same 3 sets and use 8–12 reps with a controlled tempo.' },
    ]);
    // Which quick action is highlighted
    const [activeAction, setActiveAction] = useState('Swap an exercise');

    const handleSendUserMessage = () => {
        //Implement functionality to send message (connect with backend later)
        //Store user message and AI output
        if (userInput.trim() === '') return; // ignore empty messages

        const userMessage: ChatMessage = { sender: 'user', text: userInput };
        // Placeholder reply until the backend is connected
        const aiMessage: ChatMessage = { sender: 'ai', title: 'AI reply coming soon.', text: 'This will be answered by the AI Coach once the backend is connected.' };

        setCombinedOutput(prevList => [...prevList, userMessage, aiMessage]);
        setUserInput(''); // clear the input box
    }

    // Clicking a quick action highlights it and puts its text in the input box
    const handleQuickActionClick = (action: string) => {
        setActiveAction(action);
        setUserInput(action);
    }

    return (
        <div className='ai-coach'>
            <NavBar />
            <main className='ai-coach-main'>
                <h1 className='page-title'>AI Coach</h1>
                <p className='page-subtitle'>Ask questions, swap exercises, and adapt your plan.</p>

                <div className='ai-coach-grid'>
                    {/* Left card: today's workout and quick actions */}
                    <div className='current-workout card'>
                        <h2>Current workout</h2>
                        <p className='workout-day'>{currentWorkout.name}</p>
                        <ul className='workout-exercises'>
                            {currentWorkout.exercises.map((exercise) => (
                                <li key={exercise}>{exercise}</li>
                            ))}
                        </ul>
                        <h3>Quick actions</h3>
                        {quickActions.map((action) => (
                            <button
                                key={action}
                                className={action === activeAction ? 'quick-action active' : 'quick-action'}
                                onClick={() => handleQuickActionClick(action)}
                            >
                                {action}
                            </button>
                        ))}
                    </div>

                    {/* Right card: chat history and message box */}
                    <div className='chat-card card'>
                        <div className='chat-history'>
                            {combinedOutput.map((chatMessage, index) => (
                                <div key={index} className={chatMessage.sender === 'user' ? 'message user-message' : 'message ai-message'}>
                                    {chatMessage.title && <p className='ai-title'>{chatMessage.title}</p>}
                                    <p className='message-text'>{chatMessage.text}</p>
                                </div>
                            ))}
                        </div>
                        <div className='user-message-box'>
                            <input
                                type='text'
                                placeholder='Ask FitStack anything about your plan...'
                                value={userInput}
                                onChange={(e) => setUserInput(e.target.value)}
                                // pressing Enter also sends the message
                                onKeyDown={(e) => { if (e.key === 'Enter') handleSendUserMessage(); }}
                            />
                            <button onClick={handleSendUserMessage}>Send</button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
