import type { ReactNode } from "react";
import { Button } from "./Button";
import { ApiError } from "~/types/errors";

interface ErrorMessageProps {
  error: Error | ApiError | unknown;
  onRetry?: () => void;
  className?: string;
}

export function ErrorMessage({ error, onRetry, className }: ErrorMessageProps) {
  const getErrorMessage = (err: unknown): string => {
    if (err instanceof ApiError) {
      return err.message;
    }
    if (err instanceof Error) {
      return err.message;
    }
    return "发生了未知错误";
  };

  const getErrorDetails = (err: unknown): ReactNode => {
    if (err instanceof ApiError) {
      const { code, status, details } = err;
      return (
        <div className="text-xs text-base-content/60 mt-2">
          {code && <div>错误代码: {code}</div>}
          {status && <div>HTTP 状态: {status}</div>}
          {details && (
            <details className="mt-2">
              <summary className="cursor-pointer">详细信息</summary>
              <pre className="mt-1 p-2 bg-base-300 rounded overflow-auto">
                {JSON.stringify(details, null, 2)}
              </pre>
            </details>
          )}
        </div>
      );
    }
    return null;
  };

  const message = getErrorMessage(error);
  const details = getErrorDetails(error);

  return (
    <div
      className={`card-doodle p-4 bg-error/10 border-error ${className || ""}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <svg
          className="w-5 h-5 text-error flex-shrink-0 mt-0.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-error">{message}</p>
          {details}
          {onRetry && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRetry}
              className="mt-3 text-error hover:bg-error/10"
            >
              重试
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
