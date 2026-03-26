import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense } from "react";

import "./styles/globals.css";
import { SettingsModal } from "./components/settings/SettingsModal";
import { ToastContainer } from "./components/toast/ToastContainer";
import { ErrorBoundary } from "./components/ui/ErrorBoundary";
import { LoadingOverlay } from "./components/ui/LoadingOverlay";

// 路由懒加载
const HomePage = lazy(() => import("./pages/HomePage").then(m => ({ default: m.HomePage })));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage").then(m => ({ default: m.ProjectsPage })));
const NewProjectPage = lazy(() => import("./pages/NewProjectPage").then(m => ({ default: m.NewProjectPage })));
const ProjectPage = lazy(() => import("./pages/ProjectPage").then(m => ({ default: m.ProjectPage })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Suspense fallback={<LoadingOverlay text="加载中..." />}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/project/new" element={<NewProjectPage />} />
              <Route path="/project/:id" element={<ProjectPage />} />
            </Routes>
          </Suspense>
          {/* 全局设置弹窗 - 在所有页面都可用 */}
          <SettingsModal />
          {/* 全局 Toast 通知 - 在所有页面都可用 */}
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
