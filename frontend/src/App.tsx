import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import LoginPage from "./routes/login";
import { AppLayout } from "./layout/AppLayout";
import { DashboardPage } from "./routes/dashboard";
import { EmpleadosListPage } from "./features/empleados/EmpleadosListPage";
import { EmpleadoCreateForm } from "./features/empleados/EmpleadoCreateForm";
import { EmpleadoEditPage } from "./features/empleados/EmpleadoEditPage";
import { LicenciasListPage } from "./features/licencias/LicenciasListPage";
import { LicenciaForm } from "./features/licencias/LicenciaForm";
import { LicenciaDetailPage } from "./features/licencias/LicenciaDetailPage";
import { ReportesPage } from "./features/reportes/ReportesPage";
import { AtencionesListPage } from "./features/atenciones/AtencionesListPage";
import { AtencionCreatePage } from "./features/atenciones/AtencionCreatePage";
import { AtencionDetailPage } from "./features/atenciones/AtencionDetailPage";
import { TopesPage } from "./features/admin/TopesPage";
import { UsuariosPage } from "./features/admin/UsuariosPage";
import { AreasPage } from "./features/admin/AreasPage";
import { CategoriasPage } from "./features/admin/CategoriasPage";
import { TiposLicenciaPage } from "./features/admin/TiposLicenciaPage";
import { EstudiosCatalogoPage } from "./features/admin/EstudiosCatalogoPage";
import { ConfiguracionPage } from "./features/admin/ConfiguracionPage";
import { HistoriaClinicaPage } from "./features/empleados/HistoriaClinicaPage";

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
              <Route path="/empleados/:id/editar" element={<EmpleadoEditPage />} />
              <Route path="/empleados/:id/historia-clinica" element={<HistoriaClinicaPage />} />
              <Route path="/licencias" element={<LicenciasListPage />} />
              <Route path="/licencias/nueva" element={<LicenciaForm />} />
              <Route path="/licencias/:id" element={<LicenciaDetailPage />} />
              <Route path="/atenciones" element={<AtencionesListPage />} />
              <Route path="/atenciones/nueva" element={<AtencionCreatePage />} />
              <Route path="/atenciones/:id" element={<AtencionDetailPage />} />
              <Route path="/reportes" element={<ReportesPage />} />
              <Route element={<ProtectedRoute roles={["admin"]} />}>
                <Route path="/admin/topes" element={<TopesPage />} />
                <Route path="/admin/usuarios" element={<UsuariosPage />} />
                <Route path="/admin/areas" element={<AreasPage />} />
                <Route path="/admin/categorias" element={<CategoriasPage />} />
                <Route path="/admin/tipos-licencia" element={<TiposLicenciaPage />} />
                <Route path="/admin/estudios-catalogo" element={<EstudiosCatalogoPage />} />
                <Route path="/admin/configuracion" element={<ConfiguracionPage />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
