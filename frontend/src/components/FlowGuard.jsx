import { Navigate, useLocation } from "react-router-dom";

const FlowGuard = ({ children, requiredStep }) => {
  const location = useLocation();
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  const resumeUploaded = localStorage.getItem("resumeUploaded") === "true";
  const interviewType = localStorage.getItem("interviewType");

  // 1. Auth Guard (MANDATORY)
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 2. Step Enforcement
  switch (requiredStep) {
    case 'role':
      // Dashboard/Role selection is okay if just logged in
      return children;
    
    case 'resume':
      if (!role) return <Navigate to="/role-selection" replace />;
      return children;

    case 'type':
      if (!role) return <Navigate to="/role-selection" replace />;
      if (!resumeUploaded) return <Navigate to="/resume-upload" replace />;
      return children;

    case 'interview':
      if (!role) return <Navigate to="/role-selection" replace />;
      if (!resumeUploaded) return <Navigate to="/resume-upload" replace />;
      if (!interviewType) return <Navigate to="/interview-type" replace />;
      return children;

    default:
      return children;
  }
};

export default FlowGuard;
