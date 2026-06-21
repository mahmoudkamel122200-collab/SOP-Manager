
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppRoutes } from './routes/AppRoutes';
import { MedicalBackground } from './components/MedicalBackground';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <MedicalBackground />
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
