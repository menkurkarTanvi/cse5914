import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUp.css'

export default function SignUp(){
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    // Message shown when something is missing or the passwords don't match
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const signUp = async (email: string, password: string, confirmPassword: string) => {
        // Don't try to sign up with empty fields
        if (email.trim() === '' || password === '' || confirmPassword === '') {
            setError('Please fill in all fields.');
            return;
        }
        // Both password boxes must match
        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }
        setError('');

        //handle backend logic for creating the new user account
        try{
            const response = await fetch('http://localhost:8000/users/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            if (!response.ok) {
                // FastAPI sends the reason in the "detail" field
                const data = await response.json().catch(() => null);
                // detail is a string for HTTPException, or a list for validation errors
                const message = typeof data?.detail === 'string' ? data.detail : 'Sign up failed. Please try again.';
                setError(message);
            } else {
                // Account created, so send the user to the login page
                navigate('/login');
            }
        } catch (error) {
            setError('An error occurred. Please try again.');
        }
    };

    // Runs when the form is submitted (Sign Up button or pressing Enter)
    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault(); // stop the page from reloading
        signUp(email, password, confirmPassword);
    }

    // Go back to the login page for users who already have an account
    const handleLogin = () => {
        navigate('/login');
    }

    return (
        <div className='user-signup'>
            <div className='signup-card'>
                <div className='signup-logo'>
                    <h2>FitStack</h2>
                    <p>AI Fitness Coach</p>
                </div>
                <h1>Sign up</h1>
                <p className='signup-subtitle'>Create an account to get your personalized plan.</p>

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

                    <label htmlFor="confirm-password">Confirm password</label>
                    <input
                        id="confirm-password"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                    />

                    {/* Only shows when there is an error */}
                    {error && <p className='signup-error'>{error}</p>}

                    <button type="submit" className='signup-submit-button'>Sign Up</button>
                </form>

                <p className='login-text'>Already have an account?</p>
                <button className='login-link-button' onClick={handleLogin}>Click Here to Log In</button>
            </div>
        </div>
    );
}