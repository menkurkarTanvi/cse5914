import { useState, useContext } from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Login, { AuthContext } from './Login/Login';
//import SignUp from './SignUp/SignUp';
import WorkoutPlan from './WorkoutPlan/WorkoutPlan';
import Progress from './Progress/Progress';
import AICoach from './AICoach/AICoach';
import Nutrition from './Nutrition/Nutrition';
import ProfileSetup from './Profile/Profile';
import SignUp from './SignUp/SignUp';

// Only lets logged-in users through; everyone else is sent to the login page
function ProtectedRoute() {
  const { token } = useContext(AuthContext);
  return token != null ? <Outlet /> : <Navigate to='/login' replace />;
}

export default function App2() {
  // holds the JWT token for the whole app
  const [token, setToken] = useState<string | null>(null);

  return (
    <AuthContext.Provider value={{ token, setToken }}>
      <Routes>
        {/* Public pages */}
        <Route path='/login' element={<Login />} />
        <Route path='/sign-up' element={<SignUp />} />
        
        {/* Pages that need a token (paths match the NavBar links) */}
        <Route element={<ProtectedRoute />}>
          <Route path='/my-plan' element={<WorkoutPlan />} />
          <Route path='/progress' element={<Progress />} />
          <Route path='/ai-coach' element={<AICoach />} />
          <Route path='/nutrition' element={<Nutrition />} />
          <Route path='/profile' element={<ProfileSetup />} />
        </Route>

        {/* Anything else goes to the login page */}
        <Route path='*' element={<Navigate to='/login' replace />} />
      </Routes>
    </AuthContext.Provider>
  );
}