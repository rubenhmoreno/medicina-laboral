// frontend/tests/App.test.tsx
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import LoginPage from "../src/routes/login";

vi.mock("../src/auth/AuthContext", () => ({
  useAuth: () => ({ login: vi.fn(), logout: vi.fn(), user: null, ready: true }),
}));

it("renders login form", () => {
  render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(screen.getByText("Medicia-Laboral")).toBeInTheDocument();
  expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
});
