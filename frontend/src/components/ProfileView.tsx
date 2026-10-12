import { UserIcon } from "./icons";

export default function ProfileView() {
  return (
    <div className="profile-view">
      <h2>Профіль</h2>
      <div className="profile-card">
        <div className="profile-avatar">
          <UserIcon />
        </div>
        <div>
          <h3>Гість</h3>
          <p className="muted">
            Вхід і реєстрація будуть додані пізніше (OAuth2 / Keycloak за специфікацією).
          </p>
        </div>
      </div>
    </div>
  );
}
