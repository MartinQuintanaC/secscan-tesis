import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

function LoginPage() {
  const { loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const handleLogin = async () => {
    try {
      await loginWithGoogle();
      navigate("/");
    } catch (err) {
      setError("No se pudo iniciar sesión. Inténtalo de nuevo.");
    }
  };

  return (
    <div className="login-container fade-in">
      <div className="login-box">
        <div className="login-logo-large">SS</div>
        <h1>Bienvenido a Sec<span>Scan</span></h1>
        <p className="login-subtitle">Arquitectura de Monitoreo Forense de Redes</p>
        
        {error && <div className="login-error">{error}</div>}

        <div className="login-info-box">
          <p>Para acceder al Dashboard y realizar auditorías, por favor inicia sesión con tu cuenta institucional o personal de Google.</p>
        </div>

        <button className="btn btn-primary btn-login" onClick={handleLogin}>
          <img 
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
            alt="Google" 
            className="google-icon"
          />
          Continuar con Google
        </button>
        
        <p className="login-footer">© 2026 SecScan - Proyecto de Tesis de Ingeniería</p>
      </div>
    </div>
  );
}

export default LoginPage;
