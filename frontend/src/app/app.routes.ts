import { Routes } from '@angular/router';
import { HomePageComponent } from './pages/home/home-page.component';

export const routes: Routes = [
  { path: '', component: HomePageComponent },
  {
    path: 'create',
    loadComponent: () =>
      import('./pages/create-room/create-room-page.component').then(
        m => m.CreateRoomPageComponent,
      ),
  },
  {
    path: 'join',
    loadComponent: () =>
      import('./pages/join-room/join-room-page.component').then(m => m.JoinRoomPageComponent),
  },
  {
    path: 'lobby/:code',
    loadComponent: () =>
      import('./pages/lobby/lobby-page.component').then(m => m.LobbyPageComponent),
  },
  { path: '**', redirectTo: '' },
];
