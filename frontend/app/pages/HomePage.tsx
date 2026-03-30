import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "~/services/api";
import { Button } from "~/components/ui/Button";
import { Card } from "~/components/ui/Card";
import { Layout } from "~/components/layout/Layout";
import { FilmIcon } from "@heroicons/react/24/outline";
import { useTranslation } from "react-i18next";

export function HomePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [story, setStory] = useState("");
  const [isComposing, setIsComposing] = useState(false);
  const { t } = useTranslation();

  const createMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      navigate(`/project/${project.id}?autoStart=true`);
    },
  });

  const handleSubmit = () => {
    const trimmed = story.trim();
    if (!trimmed || createMutation.isPending) return;

    const MAX_STORY_LENGTH = 5000;
    if (trimmed.length > MAX_STORY_LENGTH) {
      alert(t('project:story-too-long', { max: MAX_STORY_LENGTH, current: trimmed.length }));
      return;
    }

    const firstLine = trimmed.split("\n")[0] || "";
    const MAX_TITLE_LENGTH = 50;
    const title =
      firstLine.length > MAX_TITLE_LENGTH
        ? `${firstLine.slice(0, MAX_TITLE_LENGTH)}...`
        : firstLine;

    createMutation.mutate({
      title: title || t('project:untitled-project'),
      story: trimmed,
      style: "anime",
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Layout>
      <div className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6 lg:p-8">
        {/* Main Content */}
        <main className="w-full max-w-3xl mx-auto">
          {/* Logo / title */}
          <div className="text-center mb-8 sm:mb-10 animate-draw-in">
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-sans font-bold mb-2 inline-flex items-center gap-3">
              <FilmIcon className="w-6 h-6 sm:w-8 sm:h-8 text-secondary" aria-hidden="true" />
              <span>Hanggent Comic</span>
            </h1>
            <p className="text-base-content/80 text-base sm:text-lg mt-4 px-4">
              AI Agent Story-to-Video Platform
            </p>
          </div>

          {/* Input Card */}
          <Card
            className="w-full animate-doodle-pop"
            style={{ animationDelay: "150ms" }}
          >
            <div className="relative">
              <label htmlFor="story-input" className="sr-only">
                {t('editor:enter-story-idea')}
              </label>
              <textarea
                id="story-input"
                className="input-doodle w-full min-h-36 text-base resize-none p-4 pr-16"
                placeholder={t('editor:story-idea-placeholder')}
                value={story}
                onChange={(e) => setStory(e.target.value)}
                onKeyDown={handleKeyDown}
                onCompositionStart={() => setIsComposing(true)}
                onCompositionEnd={() => setIsComposing(false)}
                disabled={createMutation.isPending}
                aria-label={t('editor:enter-story-idea')}
                maxLength={5000}
                rows={6}
              />
              {story.length > 4500 && (
                <div className="absolute bottom-16 right-4 text-xs text-warning">
                  {t('editor:chars-remaining', { count: 5000 - story.length })}
                </div>
              )}
              <Button
                variant="primary"
                size="sm"
                className="absolute right-3 bottom-3 rounded-full !p-2 min-w-[44px] min-h-[44px] transition-all duration-200 hover:scale-110 hover:rotate-3 active:scale-95"
                onClick={handleSubmit}
                disabled={!story.trim() || createMutation.isPending}
                loading={createMutation.isPending}
                title={t('editor:start-generate')}
                aria-label={t('editor:start-generate-story')}
              >
                {!createMutation.isPending && (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="w-5 h-5"
                    aria-hidden="true"
                  >
                    <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
                  </svg>
                )}
              </Button>
            </div>
            <p className="text-xs text-base-content/50 mt-2 text-center font-sketch">
              {t('editor:enter-to-send')}
            </p>
          </Card>

          <p className="text-center text-sm text-base-content/50 mt-8 animate-fade-in" style={{ animationDelay: "300ms" }}>
            {t('editor:history-hint')}
          </p>
        </main>
      </div>
    </Layout>
  );
}