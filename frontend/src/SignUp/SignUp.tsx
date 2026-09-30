import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUp.css'

export default function SignUp(){
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    // Message shown when something is missing or the passwords don't match
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const signUp = (username: string, password: string, confirmPassword: string) => {
        // Don't try to sign up with empty fields
        if (username.trim() === '' || password === '' || confirmPassword === '') {
            setError('Please fill in all fields.');
            return;
        }
        // Both password boxes must match
        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }
        setError('');

        //handle backend logic for creating the new user account (connect with backend later)

        // Account created, so send the user to the login page
        navigate('/login');
    };

    // Runs when the form is submitted (Sign Up button or pressing Enter)
    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault(); // stop the page from reloading
        signUp(username, password, confirmPassword);
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
                    <label htmlFor="username">Username</label>
                    <input
                        id="username"
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
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