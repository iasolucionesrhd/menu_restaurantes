import { useEffect, useRef } from "react";

interface GoogleCredentialResponse {
  credential: string;
}

interface GoogleAccountsId {
  initialize: (config: { client_id: string; callback: (response: GoogleCredentialResponse) => void }) => void;
  renderButton: (parent: HTMLElement, options: { theme: string; size: string; locale: string }) => void;
}

declare global {
  interface Window {
    google?: { accounts?: { id?: GoogleAccountsId } };
  }
}

interface Props {
  onSignIn: (payload: { nombre: string; correo: string; googleIdToken: string }) => void;
}

function decodeJwtPayload(token: string): { name?: string; email?: string } {
  try {
    const [, payload] = token.split(".");
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return {};
  }
}

export function GoogleSignInButton({ onSignIn }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId || !containerRef.current) return;

    let cancelado = false;

    const intentarRenderizar = () => {
      if (cancelado || !containerRef.current) return;
      const accountsId = window.google?.accounts?.id;
      if (!accountsId) {
        // El script es async/defer: puede seguir cargando después del mount.
        setTimeout(intentarRenderizar, 100);
        return;
      }
      accountsId.initialize({
        client_id: clientId,
        callback: (response) => {
          const { name, email } = decodeJwtPayload(response.credential);
          onSignIn({ nombre: name ?? "", correo: email ?? "", googleIdToken: response.credential });
        },
      });
      accountsId.renderButton(containerRef.current, { theme: "outline", size: "large", locale: "es" });
    };

    intentarRenderizar();
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId]);

  if (!clientId) return null;

  return <div ref={containerRef} className="google-signin-button" />;
}
