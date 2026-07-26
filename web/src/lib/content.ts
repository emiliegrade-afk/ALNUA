import type {
  ContentSector,
  PostPlatform,
  PostStatus,
} from "@/components/content/content.constants";

import { hubFetch } from "./hub-fetch";

export interface Post {
  id: string;
  project_id: string;
  sector: ContentSector | null;
  author_agent_id: string | null;
  platform: PostPlatform;
  content_type: string;
  text_content: string;
  layout: Record<string, unknown> | null;
  image_prompt: string | null;
  media_urls: string[];
  video_script: string | null;
  hashtags: string[];
  channel: string | null;
  scheduled_at: string;
  published_at: string | null;
  status: PostStatus;
  created_at: string;
}

export interface GeneratePostsResponse {
  posts_created: number;
  posts: Post[];
}

export async function generatePosts(body: {
  project_id: string;
  dev_log: string;
  content_types: string[];
  platforms: string[];
  alnua_global?: boolean;
  sector?: ContentSector;
}): Promise<GeneratePostsResponse> {
  return hubFetch<GeneratePostsResponse>("/agents/content/generate", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

export async function fetchPosts(params?: {
  status?: string;
  project_id?: string;
  platform?: string;
}): Promise<Post[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.platform) qs.set("platform", params.platform);
  const query = qs.toString();
  return hubFetch<Post[]>(`/posts${query ? `?${query}` : ""}`);
}

export async function createPost(body: {
  project_id: string;
  platform: string;
  content_type: string;
  text_content: string;
  sector?: ContentSector;
  author_agent_id?: string;
  hashtags?: string[];
  layout?: Record<string, unknown>;
  media_urls?: string[];
  channel?: string;
  scheduled_at: string;
  status?: "draft" | "pending_approval" | "approved";
}): Promise<Post> {
  return hubFetch<Post>("/posts", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updatePost(
  postId: string,
  body: {
    status?: PostStatus;
    text_content?: string;
    hashtags?: string[];
    scheduled_at?: string;
    layout?: Record<string, unknown>;
    media_urls?: string[];
    channel?: string;
  }
): Promise<Post> {
  return hubFetch<Post>(`/posts/${postId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export interface CalendarResponse {
  from: string;
  to: string;
  sector: string;
  days: Record<string, Post[]>;
  total: number;
}

export async function fetchCalendar(params: {
  dateFrom: string;
  dateTo: string;
  sector?: ContentSector;
}): Promise<CalendarResponse> {
  const qs = new URLSearchParams({
    date_from: params.dateFrom,
    date_to: params.dateTo,
  });
  if (params.sector) qs.set("sector", params.sector);
  return hubFetch<CalendarResponse>(`/content/calendar?${qs.toString()}`);
}

export function computePostStats(posts: Post[]) {
  const now = new Date();
  const weekAgo = new Date(now);
  weekAgo.setDate(weekAgo.getDate() - 7);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  return {
    pending: posts.filter((p) => p.status === "pending_approval").length,
    approvedThisWeek: posts.filter(
      (p) =>
        p.status === "approved" &&
        new Date(p.created_at) >= weekAgo
    ).length,
    publishedThisMonth: posts.filter(
      (p) =>
        p.status === "published" &&
        new Date(p.published_at ?? p.created_at) >= monthStart
    ).length,
  };
}
