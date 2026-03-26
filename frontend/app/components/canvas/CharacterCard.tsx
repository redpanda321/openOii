import type { Character } from "~/types";
import { UserIcon } from "@heroicons/react/24/outline";
import { getStaticUrl } from "~/services/api";

interface CharacterCardProps {
  character: Character;
  size?: "sm" | "md" | "lg";
  selected?: boolean;
  onClick?: () => void;
}

export function CharacterCard({
  character,
  size = "md",
  selected,
  onClick,
}: CharacterCardProps) {
  const sizes = {
    sm: "w-20 h-20 sm:w-24 sm:h-24",
    md: "w-32 h-32 sm:w-36 sm:h-36 md:w-40 md:h-40",
    lg: "w-48 h-48 sm:w-56 sm:h-56 md:w-64 md:h-64",
  };
  const imageUrl = getStaticUrl(character.image_url);

  return (
    <div
      className={`card bg-base-300 cursor-pointer transition-all hover:scale-105 touch-target ${
        selected ? "ring-2 ring-primary" : ""
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
      aria-label={`选择角色 ${character.name}`}
    >
      <figure className={`${sizes[size]} flex items-center justify-center bg-base-100`}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={`${character.name}的角色形象`}
            className="object-cover w-full h-full"
            loading="lazy"
            width="256"
            height="256"
            onError={(e) => {
              // 图片加载失败时显示占位符
              e.currentTarget.style.display = "none";
              e.currentTarget.nextElementSibling?.classList.remove("hidden");
            }}
          />
        ) : null}
        <UserIcon className={`w-6 h-6 sm:w-8 sm:h-8 ${imageUrl ? "hidden" : ""}`} aria-hidden="true" />
      </figure>
      <div className="card-body p-2 sm:p-3 min-w-0">
        <h3
          className={`font-medium truncate ${
            size === "sm" ? "text-xs sm:text-sm" : "text-sm sm:text-base"
          }`}
          title={character.name}
        >
          {character.name}
        </h3>
        {size !== "sm" && character.description && (
          <p
            className="text-xs sm:text-sm text-base-content/70 line-clamp-2"
            title={character.description}
          >
            {character.description}
          </p>
        )}
      </div>
    </div>
  );
}
