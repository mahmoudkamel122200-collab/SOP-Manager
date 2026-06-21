import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthLayout } from '../layouts/AuthLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { Login } from '../pages/Login';
import { EmployeeDashboard } from '../pages/EmployeeDashboard';
import { AdminDashboard } from '../pages/AdminDashboard';
import { AdminDocuments } from '../pages/AdminDocuments';
import { AdminWarehouse } from '../pages/AdminWarehouse';
import { AdminLogs } from '../pages/AdminLogs';
import { AdminSections } from '../pages/AdminSections';
import { AdminUsers } from '../pages/AdminUsers';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
      </Route>

      {/* Employee Routes */}
      <Route element={<DashboardLayout allowedRole="EMPLOYEE" />}>
        <Route path="/employee/dashboard" element={<EmployeeDashboard />} />
      </Route>

      {/* Admin Routes */}
      <Route element={<DashboardLayout allowedRole="ADMIN" />}>
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
        <Route path="/admin/documents" element={<AdminDocuments />} />
        <Route path="/admin/warehouse" element={<AdminWarehouse />} />
        <Route path="/admin/logs" element={<AdminLogs />} />
        <Route path="/admin/sections" element={<AdminSections />} />
        <Route path="/admin/users" element={<AdminUsers />} />
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};
