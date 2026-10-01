import { createContext, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Login.css';

// Shape of the auth context: the JWT token and a function to update it
type AuthContextType = {
    token: string | null;
    setToken: (token: string | null) => void;
}

//Create an auth context
// The default value means useContext won't crash if no provider is set up yet
export const AuthContext = createContext<AuthContextType>({ token: null, setToken: () => {} });

export default function Login(){
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    // Message shown when something is missing or the login fails
    const [error, setError] = useState('');
    const { setToken } = useContext(AuthContext);
    const navigate = useNavigate();

    const login = async (email: string, password: string) => {
        // Don't try to log in with empty fields
        if (email.trim() === '' || password === '') {
            setError('Please enter your email and password.');
            return;
        }
        setError('');

        //handle backend logic for logging in user and setting the jwt token passed back
        try{
            const response = await fetch('http://localhost:8000/users/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            if(!response.ok){
                setError(data.detail || 'Login failed. Please Sign up or try again.');
            }else{
                //Store jwt token in the context so it can be used throughout the app
                setToken(data.token);
                console.log('JWT token:', data.token);
                // Login worked, so go to the dashboard
                navigate('/my-plan');
            }
        } catch (error) {
            console.error('Login error:', error);
            setError('An error occurred. Please try again.');
        }
    };

    // Runs when the form is submitted (Login button or pressing Enter)
    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault(); // stop the page from reloading
        login(email, password);
    }

    // Go to the sign-up page for users without an account
    const handleSignUp = () => {
        navigate('/sign-up');
    }

    return (
        <div className='user-login'>
            <div className='login-card'>
                <div className='login-logo'>
                    <h2>FitStack</h2>
                    <p>AI Fitness Coach</p>
                </div>
                <h1>Log in</h1>
                <p className='login-subtitle'>Welcome back. Log in to see your plan.</p>

                <form onSubmit={handleSubmit}>
                    <label htmlFor="email">Email</label>
                    <input
                        id="email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />

                    <label htmlFor="password">Password</label>
                    <input
                        id="password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />

                    {/* Only shows when there is an error */}
                    {error && <p className='login-error'>{error}</p>}

                    <button type="submit" className='login-button'>Login</button>
                </form>

                <p className='signup-text'>Don't have an account?</p>
                <button className='signup-button' onClick={handleSignUp}>Click Here to Sign Up</button>
            </div>
        </div>
    );
}