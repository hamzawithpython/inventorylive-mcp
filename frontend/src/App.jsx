import { useState } from "react";
import Login from "./Login";
import Portal from "./Portal";
import "./App.css";

export default function App() {
  const [auth, setAuth] = useState(null);

  if (!auth) {
    return (
      <Login
        onLogin={(token, role, email) => setAuth({ token, role, email })}
      />
    );
  }
  return (
    <Portal
      token={auth.token}
      role={auth.role}
      email={auth.email}
      onLogout={() => setAuth(null)}
    />
  );
}