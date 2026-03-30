import {
  LightBulbIcon,
  EyeIcon,
  SparklesIcon,
  RocketLaunchIcon,
} from "@heroicons/react/24/outline";
import type { WorkflowStage } from "~/types";
import { clsx } from "clsx";
import { useTranslation } from "react-i18next";

interface Step {
  id: WorkflowStage;
  name: string;
  labelKey: string;
  Icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

const steps: Step[] = [
  { id: "ideate", name: "Ideate", labelKey: "step-ideate", Icon: LightBulbIcon },
  { id: "visualize", name: "Visualize", labelKey: "step-visualize", Icon: EyeIcon },
  { id: "animate", name: "Animate", labelKey: "step-animate", Icon: SparklesIcon },
  { id: "deploy", name: "Deploy", labelKey: "step-deploy", Icon: RocketLaunchIcon },
];

interface WorkflowStepperProps {
  currentStage: WorkflowStage;
  isGenerating?: boolean;
  className?: string;
}

export function WorkflowStepper({
  currentStage,
  isGenerating = false,
  className,
}: WorkflowStepperProps) {
  const { t } = useTranslation('editor');
  const currentStepIndex = steps.findIndex((step) => step.id === currentStage);

  return (
    <nav aria-label="Progress" className={clsx("py-2", className)}>
      <ol role="list" className="flex items-center justify-center gap-4">
        {steps.map((step, stepIdx) => {
          const isCompleted = stepIdx < currentStepIndex;
          const isCurrent = stepIdx === currentStepIndex;

          return (
            <li key={step.name} className="flex flex-col items-center gap-1">
              <div
                className={clsx(
                  "flex h-10 w-10 items-center justify-center rounded-full border-3 border-black transition-all duration-200",
                  isCurrent && isGenerating && "animate-pulse",
                  isCurrent
                    ? "bg-primary shadow-brutal scale-110"
                    : isCompleted
                      ? "bg-secondary"
                      : "bg-base-300",
                   isCurrent && isGenerating && "!bg-warning"
                )}
              >
                {isCompleted ? (
                   <span className="font-bold text-lg text-base-content">✓</span>
                ) : (
                  <step.Icon
                    className={clsx(
                      "h-6 w-6",
                      isCurrent ? "text-base-content" : "text-base-content/50"
                    )}
                    aria-hidden="true"
                  />
                )}
              </div>
               <span
                className={clsx(
                  "text-xs font-heading font-bold transition-colors",
                  isCurrent ? "text-primary" : "text-base-content/60"
                )}
              >
                {t(step.labelKey)}
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}