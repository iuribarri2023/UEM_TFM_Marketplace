import { Routes } from '@angular/router';
import { adminGuard, manufacturerGuard } from './core/auth/role.guards';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'catalogue' },
  {
    path: 'catalogue',
    loadComponent: () =>
      import('./features/catalogue/catalogue-page').then((m) => m.CataloguePage),
  },
  {
    path: 'generic-solutions/:code',
    loadComponent: () =>
      import('./features/catalogue/generic-detail-page').then((m) => m.GenericDetailPage),
  },
  {
    path: 'marketplace',
    loadComponent: () =>
      import('./features/marketplace/marketplace-page').then((m) => m.MarketplacePage),
  },
  {
    path: 'marketplace/:id',
    loadComponent: () =>
      import('./features/marketplace/commercial-detail-page').then((m) => m.CommercialDetailPage),
  },
  {
    path: 'manufacturers',
    loadComponent: () =>
      import('./features/manufacturers/manufacturers-page').then((m) => m.ManufacturersPage),
  },
  {
    path: 'manufacturers/:id',
    loadComponent: () =>
      import('./features/manufacturers/manufacturer-detail-page').then(
        (m) => m.ManufacturerDetailPage,
      ),
  },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login-page').then((m) => m.LoginPage),
  },
  {
    path: 'manufacturer/solutions',
    canActivate: [manufacturerGuard],
    loadComponent: () =>
      import('./features/manufacturer-workspace/solution-list-page').then(
        (m) => m.ManufacturerSolutionListPage,
      ),
  },
  {
    path: 'manufacturer/solutions/new',
    canActivate: [manufacturerGuard],
    loadComponent: () =>
      import('./features/manufacturer-workspace/solution-create-page').then(
        (m) => m.ManufacturerSolutionCreatePage,
      ),
  },
  {
    path: 'manufacturer/solutions/:id/edit',
    canActivate: [manufacturerGuard],
    loadComponent: () =>
      import('./features/manufacturer-workspace/solution-edit-page').then(
        (m) => m.ManufacturerSolutionEditPage,
      ),
  },
  {
    path: 'admin/review',
    canActivate: [adminGuard],
    loadComponent: () =>
      import('./features/admin-review/admin-review-page').then((m) => m.AdminReviewPage),
  },
  {
    path: '**',
    loadComponent: () => import('./features/not-found-page').then((m) => m.NotFoundPage),
  },
];
