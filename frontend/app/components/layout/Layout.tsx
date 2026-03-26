import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { useSidebarStore } from "~/stores/sidebarStore";

interface LayoutProps {
  children: ReactNode;
  /** 是否显示侧边栏，默认 true */
  showSidebar?: boolean;
}

export function Layout({ children, showSidebar = true }: LayoutProps) {
  const { isOpen } = useSidebarStore();

  if (!showSidebar) {
    return (
      <>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-content focus:rounded-lg focus:shadow-brutal"
        >
          跳到主内容
        </a>
        <main id="main-content" tabIndex={-1}>
          {children}
        </main>
      </>
    );
  }

  return (
    <div className="min-h-screen bg-base-100">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-content focus:rounded-lg focus:shadow-brutal"
      >
        跳到主内容
      </a>
      <Sidebar />
      <main
        id="main-content"
        tabIndex={-1}
        className={`min-h-screen transition-all duration-300 ease-in-out ${
          isOpen ? "ml-72" : "ml-0"
        }`}
      >
        {children}
      </main>
    </div>
  );
}
