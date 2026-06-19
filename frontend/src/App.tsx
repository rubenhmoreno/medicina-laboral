import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import LoginPage from "./routes/login";
import { AppLayout } from "./layout/AppLayout";
import { DashboardPage } from "./routes/dashboard";
import { EmpleadosListPage } from "./features/empleados/EmpleadosListPage";
import { EmpleadoCreateForm } from "./features/empleados/EmpleadoCreateForm";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/empleados" element={<EmpleadosListPage />} />
              <Route path="/empleados/nuevo" element={<EmpleadoCreateForm />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
