import { Injectable } from '@angular/core';

interface ApiError {
  status?: number;
  error?: {
    code?: string;
    message?: string;
    detail?: string;
  };
}

const ERROR_MESSAGES: Readonly<Record<string, string>> = {
  room_not_found: 'Code de salle invalide. Vérifie le code et réessaie.',
  room_already_started: 'La partie a déjà commencé. Tu ne peux plus rejoindre.',
  nickname_taken: 'Ce pseudo est déjà pris. Choisis-en un autre.',
  room_not_waiting: 'La partie a déjà commencé.',
  round_not_finished: "La manche n'est pas encore terminée.",
  round_not_found: 'Manche introuvable.',
  round_not_in_progress: 'Aucune manche en cours.',
  song_not_found: 'Chanson introuvable.',
  song_not_playable: 'Cette chanson ne peut pas être lancée.',
  answer_too_late: 'Trop tard ! La chanson est terminée.',
  song_not_locked: "La chanson n'est pas encore terminée.",
  song_not_correctable: 'Les réponses ne peuvent plus être modifiées.',
  song_not_revealable: 'La chanson ne peut pas encore être révélée.',
  not_host: "Action réservée à l'hôte.",
  answer_not_found: 'Réponse introuvable.',
  internal_error: 'Erreur inattendue. Réessaie dans quelques instants.',
};

@Injectable({ providedIn: 'root' })
export class ErrorService {
  readonly wsDisconnected = 'Connexion perdue. Actualise la page pour rejoindre.';
  readonly audioBlocked = "Son bloqué par le navigateur. Clique sur la page pour lancer l'audio.";
  readonly deezerUnavailable =
    'Musique temporairement indisponible. La partie continue avec des chansons de remplacement.';

  fromHttpError(err: ApiError): string {
    const code = err.error?.code;
    if (code) {
      return this.fromCode(code) ?? err.error?.message ?? 'Erreur inattendue.';
    }
    if (err.error?.detail) {
      return err.error.detail;
    }
    return 'Erreur inattendue.';
  }

  fromCode(code: string): string | null {
    return ERROR_MESSAGES[code] ?? null;
  }
}
