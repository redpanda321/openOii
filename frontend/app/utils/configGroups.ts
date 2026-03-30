import type { ConfigItem } from "~/types";
import i18n from '~/i18n';

export interface ConfigSection {
  key: string;
  title: string;
  items: ConfigItem[];
}

export function groupConfigs(configs: ConfigItem[]): ConfigSection[] {
  const groups: Record<string, ConfigItem[]> = {
    database: [],
    text: [],
    image: [],
    video: [],
  };

  configs.forEach((config) => {
    const key = config.key.toLowerCase();

    // 数据库配置
    if (key.startsWith("database_") || key.startsWith("redis_") || key.startsWith("db_")) {
      groups.database.push(config);
    }
    // 文本生成服务配置（Anthropic + OpenAI 兼容）
    else if (key.startsWith("anthropic_") || key.startsWith("text_")) {
      groups.text.push(config);
    }
    // 图像服务配置
    else if (key.startsWith("image_") || key === "enable_image_to_image") {
      groups.image.push(config);
    }
    // 视频服务配置
    else if (
      key.startsWith("video_") ||
      key.startsWith("doubao_") ||
      key === "enable_image_to_video"
    ) {
      groups.video.push(config);
    }
    // 其他配置项忽略（基础设置、其他设置不显示）
  });

  return [
    { key: "database", title: i18n.t('setting:database'), items: groups.database },
    { key: "text", title: i18n.t('setting:text-generation'), items: groups.text },
    { key: "image", title: i18n.t('setting:image-generation'), items: groups.image },
    { key: "video", title: i18n.t('setting:video-service'), items: groups.video },
  ].filter((section) => section.items.length > 0); // 过滤空分组
}
