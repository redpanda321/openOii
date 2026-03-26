import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "~/services/api";
import { Button } from "~/components/ui/Button";
import { Card } from "~/components/ui/Card";
import { Layout } from "~/components/layout/Layout";
import { FilmIcon, SparklesIcon } from "@heroicons/react/24/outline";

export function HomePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [story, setStory] = useState("");
  const [isComposing, setIsComposing] = useState(false);

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

    // 输入验证：长度限制
    const MAX_STORY_LENGTH = 5000;
    if (trimmed.length > MAX_STORY_LENGTH) {
      alert(`故事太长了！请控制在 ${MAX_STORY_LENGTH} 字以内（当前 ${trimmed.length} 字）`);
      return;
    }

    const firstLine = trimmed.split("\n")[0] || "";
    const MAX_TITLE_LENGTH = 50;
    const title =
      firstLine.length > MAX_TITLE_LENGTH
        ? `${firstLine.slice(0, MAX_TITLE_LENGTH)}...`
        : firstLine;

    createMutation.mutate({
      title: title || "未命名项目",
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
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-heading font-bold mb-2 relative inline-block">
              <span className="text-primary absolute -top-3 sm:-top-4 -left-4 sm:-left-6 text-2xl sm:text-3xl transform -rotate-12 animate-wiggle">
                <FilmIcon className="w-5 h-5 sm:w-6 sm:h-6" aria-hidden="true" />
              </span>
              <span className="underline-sketch">openOii</span>
              <span className="text-secondary absolute -bottom-3 sm:-bottom-4 -right-4 sm:-right-6 text-2xl sm:text-3xl transform rotate-12 animate-wiggle">
                <SparklesIcon className="w-5 h-5 sm:w-6 sm:h-6" aria-hidden="true" />
              </span>
            </h1>
            <p className="text-base-content/80 font-sketch text-base sm:text-lg mt-4 px-4">
              用 AI Agent 将你的故事转化为动漫视频
            </p>
          </div>

          {/* Input Card */}
          <Card
            className="w-full animate-doodle-pop"
            style={{ animationDelay: "150ms" }}
          >
            <div className="relative">
              <label htmlFor="story-input" className="sr-only">
                输入你的故事创意
              </label>
              <textarea
                id="story-input"
                className="input-doodle w-full min-h-36 text-base resize-none p-4 pr-16"
                placeholder={
                  "写下你的故事创意\n\n例如：一只梦想成为宇航员的猫，偷偷登上了火箭..."
                }
                value={story}
                onChange={(e) => setStory(e.target.value)}
                onKeyDown={handleKeyDown}
                onCompositionStart={() => setIsComposing(true)}
                onCompositionEnd={() => setIsComposing(false)}
                disabled={createMutation.isPending}
                aria-label="输入你的故事创意"
                maxLength={5000}
                rows={6}
              />
              {story.length > 4500 && (
                <div className="absolute bottom-16 right-4 text-xs text-warning">
                  还能写 {5000 - story.length} 字
                </div>
              )}
              <Button
                variant="primary"
                size="sm"
                className="absolute right-3 bottom-3 rounded-full !p-2 min-w-[44px] min-h-[44px] transition-all duration-200 hover:scale-110 hover:rotate-3 active:scale-95"
                onClick={handleSubmit}
                disabled={!story.trim() || createMutation.isPending}
                loading={createMutation.isPending}
                title="开始生成 (Enter)"
                aria-label="开始生成故事"
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
              按 Enter 发送，Shift + Enter 换行
            </p>
          </Card>

          {/* 提示文字 */}
          <p className="text-center text-sm text-base-content/50 mt-8 animate-fade-in" style={{ animationDelay: "300ms" }}>
            历史记录在左侧边栏中查看 ←
          </p>
        </main>
      </div>
    </Layout>
  );
}
