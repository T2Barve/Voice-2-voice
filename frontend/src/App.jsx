import { Routes, Route, BrowserRouter } from "react-router-dom";
import LandingPage from "./pages/LandingPage.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import RoleSelectionPage from "./pages/RoleSelectionPage.jsx";
import ResumeUploadPage from "./pages/ResumeUploadPage.jsx";
import InterviewTypePage from "./pages/InterviewTypePage.jsx";
import InterviewPage from "./pages/InterviewPage.jsx";
import FlowGuard from "./components/FlowGuard.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/signup" element={<AuthPage mode="signup" />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          
          <Route path="/role-selection" element={
            <FlowGuard requiredStep="role">
              <RoleSelectionPage />
            </FlowGuard>
          } />
          
          <Route path="/resume-upload" element={
            <FlowGuard requiredStep="resume">
              <ResumeUploadPage />
            </FlowGuard>
          } />
          
          <Route path="/interview-type" element={
            <FlowGuard requiredStep="type">
              <InterviewTypePage />
            </FlowGuard>
          } />
          
          <Route path="/interview" element={
            <FlowGuard requiredStep="interview">
              <InterviewPage />
            </FlowGuard>
          } />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
