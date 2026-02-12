import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import Projects from './pages/Projects';
import Modules from './pages/Modules';
import Settings from './pages/Settings';

import ProjectWorkspace from './pages/ProjectWorkspace';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<AppLayout />}>
                    <Route index element={<Navigate to="/projects" replace />} />
                    <Route path="projects" element={<Projects />} />
                    <Route path="projects/:id" element={<ProjectWorkspace />} />
                    <Route path="modules" element={<Modules />} />
                    <Route path="settings" element={<Settings />} />
                    {/* Fallback */}
                    <Route path="*" element={<Navigate to="/projects" replace />} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
